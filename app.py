from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
import smtplib
from datetime import datetime
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

class Birthday(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    date = db.Column(db.String(10))  # Format: MM-DD

def send_email(name, email):
    sender_email = "your_email@gmail.com"
    sender_password = "your_app_password"
    subject = "🎉 Birthday Reminder!"
    message = f"Today is {name}'s birthday! Don't forget to wish them. 🥳"

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(sender_email, sender_password)
        smtp.sendmail(sender_email, email, f"Subject: {subject}\n\n{message}")

def check_birthdays():
    today = datetime.now().strftime("%m-%d")
    birthdays = Birthday.query.filter_by(date=today).all()
    for birthday in birthdays:
        send_email(birthday.name, birthday.email)

scheduler = BackgroundScheduler()
scheduler.add_job(func=check_birthdays, trigger="interval", hours=24)
scheduler.start()

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        date = request.form["date"]  # Expecting MM-DD
        new_birthday = Birthday(name=name, email=email, date=date)
        db.session.add(new_birthday)
        db.session.commit()
        return redirect("/")
    birthdays = Birthday.query.all()
    return render_template("index.html", birthdays=birthdays)

if __name__ == "__main__":
    if not os.path.exists("database.db"):
        db.create_all()
    app.run(debug=True)
