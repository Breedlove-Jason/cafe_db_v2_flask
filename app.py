# from form import CafeForm
import os

from dotenv import load_dotenv
from flask import Flask
from flask_bootstrap import Bootstrap  # Change to Flask-Bootstrap
from flask_sqlalchemy import SQLAlchemy

load_dotenv()
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
Bootstrap(app)
db = SQLAlchemy(app)


class Cafe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    location = db.Column(db.String(250), nullable=False)
    open_time = db.Column(db.String(100), nullable=False)
    close_time = db.Column(db.String(100), nullable=False)
    coffee_rating = db.Column(db.String(10), nullable=False)
    wifi_rating = db.Column(db.String(10), nullable=False)
    power_rating = db.Column(db.String(10), nullable=False)


with app.app_context():
    db.create_all()


@app.route("/")
def hello_world():  # put application's code here
    return "Hello World!"


if __name__ == "__main__":
    app.run()
