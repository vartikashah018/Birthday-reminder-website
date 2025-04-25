from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, date
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///birthdays.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('GMAIL_USER')
app.config['MAIL_PASSWORD'] = os.getenv('GMAIL_PASSWORD')

db = SQLAlchemy(app)


# Birthday Model
class Birthday(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    notify_days_before = db.Column(db.Integer, default=1)
    notes = db.Column(db.Text)

    def __repr__(self):
        return f'<Birthday {self.name}>'


# Create database tables
with app.app_context():
    db.create_all()


# Email sending function
def send_birthday_reminder(recipient_email, name, birth_date, days_until):
    subject = f"Birthday Reminder: {name}'s birthday is coming up!"
    body = f"""
    <html>
        <body>
            <h2>Birthday Reminder</h2>
            <p>{name}'s birthday is on {birth_date.strftime('%B %d')}.</p>
            <p>That's in {days_until} day{'s' if days_until != 1 else ''}!</p>
        </body>
    </html>
    """

    msg = MIMEMultipart()
    msg['From'] = app.config['MAIL_USERNAME']
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))

    try:
        with smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT']) as server:
            server.starttls()
            server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            server.send_message(msg)
        print(f"Reminder sent for {name}'s birthday")
    except Exception as e:
        print(f"Failed to send email: {e}")


# Check birthdays function
def check_birthdays():
    with app.app_context():
        today = date.today()
        birthdays = Birthday.query.all()

        for birthday in birthdays:
            next_birthday = date(today.year, birthday.birth_date.month, birthday.birth_date.day)

            # If birthday already passed this year, check next year
            if next_birthday < today:
                next_birthday = date(today.year + 1, birthday.birth_date.month, birthday.birth_date.day)

            days_until = (next_birthday - today).days

            # Check if we should send a reminder today
            if days_until <= birthday.notify_days_before:
                send_birthday_reminder(
                    birthday.email,
                    birthday.name,
                    next_birthday,
                    days_until
                )


# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=check_birthdays, trigger='cron', hour=9, minute=0)  # Run daily at 9 AM
scheduler.start()


# Routes
@app.route('/')
def index():
    birthdays = Birthday.query.order_by(Birthday.birth_date).all()
    today = date.today()

    # Calculate days until next birthday for each entry
    for birthday in birthdays:
        next_birthday = date(today.year, birthday.birth_date.month, birthday.birth_date.day)
        if next_birthday < today:
            next_birthday = date(today.year + 1, birthday.birth_date.month, birthday.birth_date.day)
        birthday.days_until = (next_birthday - today).days

    return render_template('index.html', birthdays=birthdays, today=today)


@app.route('/add', methods=['GET', 'POST'])
def add_birthday():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        birth_date = datetime.strptime(request.form['birth_date'], '%Y-%m-%d').date()
        notify_days_before = int(request.form['notify_days_before'])
        notes = request.form.get('notes', '')

        new_birthday = Birthday(
            name=name,
            email=email,
            birth_date=birth_date,
            notify_days_before=notify_days_before,
            notes=notes
        )

        db.session.add(new_birthday)
        db.session.commit()

        flash('Birthday added successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('add_edit.html')


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_birthday(id):
    birthday = Birthday.query.get_or_404(id)

    if request.method == 'POST':
        birthday.name = request.form['name']
        birthday.email = request.form['email']
        birthday.birth_date = datetime.strptime(request.form['birth_date'], '%Y-%m-%d').date()
        birthday.notify_days_before = int(request.form['notify_days_before'])
        birthday.notes = request.form.get('notes', '')

        db.session.commit()

        flash('Birthday updated successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('add_edit.html', birthday=birthday)


@app.route('/delete/<int:id>')
def delete_birthday(id):
    birthday = Birthday.query.get_or_404(id)
    db.session.delete(birthday)
    db.session.commit()

    flash('Birthday deleted successfully!', 'success')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)