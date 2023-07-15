from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func


class Staff(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(1000), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(50), nullable=False)
    isAdmin = db.Column(db.Boolean, nullable=False, default=False)
    adder = db.relationship("PaymentData")


class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    call_name = db.Column(db.String(50), nullable=False, unique=True)
    is_archived = db.Column(db.Boolean, nullable=False, default=False)
    deadline_pembayaran = db.Column(db.Integer, nullable=True, default=0)
    paid_data = db.relationship("PaymentData")


class Year(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    year_name = db.Column(db.String(10), nullable=False, unique=True)
    months = db.relationship("Month")
    payment_made_yearly = db.relationship("PaymentData")


class Month(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    month_name = db.Column(db.String, nullable=False)
    year_id = db.Column(db.ForeignKey("year.id"))
    payment_data = db.relationship("PaymentData")


class PaymentData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    paid_month = db.Column(db.ForeignKey("month.id"), nullable=False)
    paid_year = db.Column(db.ForeignKey("year.id"), nullable=False)
    payer = db.Column(db.ForeignKey("client.id"), nullable=False)
    states = db.Column(db.String(20), nullable=False, default="belum lunas")
    isPaid = db.Column(db.Boolean, nullable=False, default=False)
    date_paid = db.Column(db.String(20), nullable=True)
    last_edit_by = db.Column(db.ForeignKey("staff.id"))
    last_edit_date = db.Column(db.Date, nullable=False, default=func.current_date())
