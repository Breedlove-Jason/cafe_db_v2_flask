import os
from form import CafeForm
from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for, flash
from flask_bootstrap import Bootstrap  # Change to Flask-Bootstrap
from flask_sqlalchemy import SQLAlchemy

load_dotenv()
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///cafes.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
Bootstrap(app)
db = SQLAlchemy(app)


class Cafe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(
        db.String(250), nullable=False, unique=True
    )  # Add unique constraint
    location = db.Column(db.String(250), nullable=False)
    open_time = db.Column(db.String(100), nullable=False)
    close_time = db.Column(db.String(100), nullable=False)
    coffee_rating = db.Column(db.String(10), nullable=False)
    wifi_rating = db.Column(db.String(10), nullable=False)
    power_rating = db.Column(db.String(10), nullable=False)


with app.app_context():
    db.create_all()


@app.route("/")
def home():
    cafes = Cafe.query.all()
    return render_template("index.html", cafes=cafes)


@app.route("/add", methods=["GET", "POST"])
def add_cafe():
    form = CafeForm()
    if form.validate_on_submit():
        new_cafe = Cafe(
            name=form.name.data,
            location=form.location.data,
            open_time=form.open_time.data,
            close_time=form.close_time.data,
            coffee_rating=form.coffee_rating.data,
            wifi_rating=form.wifi_rating.data,
            power_rating=form.power_rating.data,
        )
        db.session.add(new_cafe)
        db.session.commit()
        flash("Cafe added successfully!", "success")
        return redirect(url_for("home"))
    return render_template("add.html", form=form)


@app.route("/delete/<int:cafe_id>")
def delete_cafe(cafe_id):
    cafe_to_delete = Cafe.query.get(cafe_id)
    db.session.delete(cafe_to_delete)
    db.session.commit()
    flash("Cafe deleted successfully!", "success")
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)
