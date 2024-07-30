from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired, URL, Regexp

# Define constants for choices to improve readability
COFFEE_RATINGS = ["☕", "☕☕", "☕☕☕", "☕☕☕☕", "☕☕☕☕☕"]
WIFI_RATINGS = ["💪", "💪💪", "💪💪💪", "💪💪💪💪", "💪💪💪💪💪"]
POWER_RATINGS = ["🔌", "🔌🔌", "🔌🔌🔌", "🔌🔌🔌🔌", "🔌🔌🔌🔌🔌"]


class CafeForm(FlaskForm):
    name = StringField("Cafe name", validators=[DataRequired()])
    location = StringField(
        "Cafe Location on Google Maps (URL)", validators=[DataRequired(), URL()]
    )
    open_time = StringField(
        "Opening Time e.g. 8AM",
        validators=[DataRequired(), Regexp(r"^(0[0-9]|1[0-2]):[0-5][0-9] (AM|PM)$")],
    )
    close_time = StringField(
        "Closing Time e.g. 5PM",
        validators=[DataRequired(), Regexp(r"^(0[0-9]|1[0-2]):[0-5][0-9] (AM|PM)$")],
    )
    coffee_rating = SelectField(
        "Coffee Rating",
        choices=[(rating, rating) for rating in COFFEE_RATINGS],
        validators=[DataRequired()],
    )
    wifi_rating = SelectField(
        "Wifi Strength Rating",
        choices=[(rating, rating) for rating in WIFI_RATINGS],
        validators=[DataRequired()],
    )
    power_rating = SelectField(
        "Power Socket Availability",
        choices=[(rating, rating) for rating in POWER_RATINGS],
        validators=[DataRequired()],
    )
    submit = SubmitField("Submit")
