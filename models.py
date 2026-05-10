from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(80), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    new_device = db.Column(db.Boolean, default=False)
    location_mismatch = db.Column(db.Boolean, default=False)
    failed_logins_24h = db.Column(db.Integer, default=0)
    risk_score = db.Column(db.Float, nullable=False)
    decision = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SimSwapEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(80), nullable=False)
    sim_swap_count_30d = db.Column(db.Integer, nullable=False)
    hours_since_sim_change = db.Column(db.Float, nullable=False)
    risk_score = db.Column(db.Float, nullable=False)
    decision = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(80), nullable=False)
    event_type = db.Column(db.String(50), nullable=False) # e.g., 'TRANSACTION', 'SIM_SWAP'
    message = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    account_balance = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class OTPVerification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.String(80), nullable=False)
    transaction_id = db.Column(db.Integer, nullable=True) # ID of pending transaction
    otp_code = db.Column(db.String(10), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
