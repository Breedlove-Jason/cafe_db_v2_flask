"""BrewDesk: searchable SQL catalog + private browser workspace."""
import csv
import json
import os
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

import click
from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint, select, func
from sqlalchemy.pool import StaticPool

ROOT = Path(__file__).resolve().parent
db = SQLAlchemy()


class Cafe(db.Model):
    __tablename__ = "brewdesk_cafes"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    location = db.Column(db.String(500), nullable=False)
    open_time = db.Column(db.String(5), nullable=False)
    close_time = db.Column(db.String(5), nullable=False)
    coffee_rating = db.Column(db.Integer, nullable=False)
    wifi_rating = db.Column(db.Integer, nullable=False)
    power_rating = db.Column(db.Integer, nullable=False)
    sample = db.Column(db.Boolean, nullable=False, default=True)
    __table_args__ = tuple(CheckConstraint(f"{field}_rating BETWEEN 0 AND 5") for field in ("coffee", "wifi", "power"))

    def as_dict(self):
        return {key: getattr(self, key) for key in ("id", "name", "location", "open_time", "close_time", "coffee_rating", "wifi_rating", "power_rating", "sample")}


def valid_url(value):
    parsed = urlsplit(value)
    return parsed.scheme == "https" and bool(parsed.hostname) and not parsed.username and not parsed.password


def parse_time(value):
    compact = value.strip().upper().replace(" ", "")
    for fmt in ("%I:%M%p", "%I%p", "%H:%M"):
        try:
            return datetime.strptime(compact, fmt).strftime("%H:%M")
        except ValueError:
            pass
    raise ValueError(f"Invalid opening/closing time: {value}")


def parse_legacy_csv(path):
    """Convert original emoji ratings and times, validating every row first."""
    cafes = []
    with open(path, encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            name, location = row["Cafe Name"].strip(), row["Location"].strip()
            if not name or len(name) > 120 or not valid_url(location):
                raise ValueError("Cafe requires a name and a valid HTTPS map link")
            ratings = {f"{key}_rating": row[label].count(icon) for key, label, icon in
                       (("coffee", "Coffee", "☕"), ("wifi", "Wifi", "💪"), ("power", "Power", "🔌"))}
            if any(rating > 5 for rating in ratings.values()):
                raise ValueError("Ratings must be between zero and five")
            cafes.append(dict(name=name, location=location, open_time=parse_time(row["Open"]),
                              close_time=parse_time(row["Close"]), sample=True, **ratings))
    if len({cafe["name"].casefold() for cafe in cafes}) != len(cafes):
        raise ValueError("Duplicate cafe names in input")
    return cafes


def create_app(config=None):
    app = Flask(__name__, static_folder="public/static", static_url_path="/static")
    url = os.getenv("DATABASE_URL", "").strip()
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            url = "postgresql+psycopg://" + url[len(prefix):]
            break
    app.config.update(SQLALCHEMY_DATABASE_URI=url or "sqlite://", SQLALCHEMY_TRACK_MODIFICATIONS=False,
                      SAMPLE_CATALOG=not bool(url), MAX_CONTENT_LENGTH=32768)
    if config:
        app.config.update(config)
    if app.config["SQLALCHEMY_DATABASE_URI"] == "sqlite://":
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"poolclass": StaticPool, "connect_args": {"check_same_thread": False}}
    db.init_app(app)
    # Only the isolated sample database is created at startup; external databases
    # are initialized explicitly with the CLI, never during an HTTP request.
    if app.config["SAMPLE_CATALOG"]:
        with app.app_context():
            db.create_all()
            db.session.add_all(Cafe(**item) for item in json.loads((ROOT / "data/catalog.json").read_text()))
            db.session.commit()

    @app.get("/")
    def home():
        return render_template("index.html")

    @app.get("/api/cafes")
    def cafes():
        query = request.args.get("q", "").strip()
        if len(query) > 120:
            return jsonify(error="Search must be 120 characters or fewer."), 400
        filters = {}
        for key in ("coffee", "wifi", "power"):
            raw = request.args.get(key, "0")
            if raw not in {"0", "1", "2", "3", "4", "5"}:
                return jsonify(error="Ratings must be whole numbers from 0 to 5."), 400
            filters[key] = int(raw)
        sort = request.args.get("sort", "work")
        if sort not in {"work", "coffee", "wifi", "power", "name"}:
            return jsonify(error="Unknown sort order."), 400
        statement = select(Cafe)
        if query:
            statement = statement.where(func.lower(Cafe.name).contains(query.lower(), autoescape=True))
        for key, rating in filters.items():
            statement = statement.where(getattr(Cafe, f"{key}_rating") >= rating)
        order = {"work": (Cafe.wifi_rating + Cafe.power_rating).desc(), "coffee": Cafe.coffee_rating.desc(),
                 "wifi": Cafe.wifi_rating.desc(), "power": Cafe.power_rating.desc(), "name": func.lower(Cafe.name)}[sort]
        rows = db.session.scalars(statement.order_by(order, func.lower(Cafe.name)).limit(200)).all()
        return jsonify(cafes=[row.as_dict() for row in rows], count=len(rows), sample_catalog=app.config["SAMPLE_CATALOG"])

    @app.get("/health")
    def health():
        db.session.execute(select(1))
        return jsonify(status="ok")

    @app.after_request
    def headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        return response

    @app.cli.command("init-db")
    def init_db():
        """Create only BrewDesk tables in the configured database."""
        db.create_all()
        click.echo("BrewDesk tables are ready.")

    @app.cli.command("import-legacy")
    @click.argument("path", type=click.Path(exists=True, dir_okay=False))
    def import_legacy(path):
        """Import original CSV; existing names are preserved, never overwritten."""
        try:
            items = parse_legacy_csv(path)
        except (ValueError, KeyError) as error:
            raise click.ClickException(str(error)) from error
        added = 0
        for item in items:
            if not db.session.scalar(select(Cafe).where(func.lower(Cafe.name) == item["name"].lower())):
                db.session.add(Cafe(**item))
                added += 1
        db.session.commit()
        click.echo(f"Imported {added} cafes; existing entries preserved.")

    return app


app = create_app()
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5000")))
