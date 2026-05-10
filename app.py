from __future__ import annotations

import functools
import jwt
import datetime
import random
import string
from flask import Flask, jsonify, request, render_template
from werkzeug.security import generate_password_hash, check_password_hash

from risk_engine import RiskEngine
from models import db, User, Transaction, SimSwapEvent, Alert, Customer, OTPVerification
from sms_service import send_sms

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sim_swap.db'
app.config['SECRET_KEY'] = 'super-secret-sim-swap-key'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
engine = RiskEngine()

with app.app_context():
    db.create_all()
    if not Customer.query.filter_by(customer_id="CUST-001").first():
        import os
        my_phone = os.getenv("MY_PHONE_NUMBER", "+1234567890")
        test_cust = Customer(customer_id="CUST-001", name="Test User", phone_number=my_phone, account_balance=10000)
        db.session.add(test_cust)
        db.session.commit()

def token_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            if "Bearer " in token:
                token = token.split(" ")[1]
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.filter_by(id=data['user_id']).first()
        except Exception as e:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

@app.post("/api/auth/register")
def register():
    data = request.get_json(silent=True) or {}
    if not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Missing username or password'}), 400
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'User already exists'}), 400
        
    hashed_password = generate_password_hash(data['password'])
    new_user = User(username=data['username'], password_hash=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'Registered successfully'}), 201

@app.post("/api/auth/login")
def login():
    data = request.get_json(silent=True) or {}
    if not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Missing username or password'}), 400
        
    user = User.query.filter_by(username=data['username']).first()
    if not user or not check_password_hash(user.password_hash, data['password']):
        return jsonify({'message': 'Invalid credentials'}), 401
        
    token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, app.config['SECRET_KEY'], algorithm="HS256")
    
    return jsonify({'token': token}), 200

@app.get("/")
@app.get("/dashboard")
def dashboard():
    return render_template("index.html")

@app.get("/api/dashboard/data")
def dashboard_data():
    transactions = Transaction.query.order_by(Transaction.created_at.desc()).limit(10).all()
    sim_swaps = SimSwapEvent.query.order_by(SimSwapEvent.created_at.desc()).limit(10).all()
    alerts = Alert.query.order_by(Alert.created_at.desc()).limit(10).all()
    
    return jsonify({
        "transactions": [{"user_id": t.user_id, "amount": t.amount, "decision": t.decision, "risk_score": t.risk_score, "time": t.created_at.isoformat()} for t in transactions],
        "sim_swaps": [{"user_id": s.user_id, "decision": s.decision, "risk_score": s.risk_score, "time": s.created_at.isoformat()} for s in sim_swaps],
        "alerts": [{"user_id": a.user_id, "event_type": a.event_type, "message": a.message, "time": a.created_at.isoformat()} for a in alerts]
    })


def _validate_payload(data: dict):
    required = [
        "user_id",
        "sim_swap_count_30d",
        "hours_since_sim_change",
        "new_device",
        "location_mismatch",
        "failed_logins_24h",
        "transaction_amount",
    ]
    missing = [k for k in required if k not in data]
    if missing:
        return False, f"Missing fields: {', '.join(missing)}"
    return True, ""


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "sim-swap-risk-engine"}), 200


@app.post("/api/risk/evaluate")
@token_required
def evaluate_risk(current_user):
    data = request.get_json(silent=True) or {}
    ok, message = _validate_payload(data)
    if not ok:
        return jsonify({"error": message}), 400

    decision = engine.evaluate(data)
    
    # Save transaction to DB
    new_tx = Transaction(
        user_id=data["user_id"],
        amount=float(data.get("transaction_amount", 0)),
        new_device=bool(data.get("new_device", False)),
        location_mismatch=bool(data.get("location_mismatch", False)),
        failed_logins_24h=int(data.get("failed_logins_24h", 0)),
        risk_score=decision.score,
        decision=decision.decision
    )
    db.session.add(new_tx)
    
    if decision.decision == "STEP_UP":
        customer = Customer.query.filter_by(customer_id=data["user_id"]).first()
        if not customer:
            import os
            my_phone = os.getenv("MY_PHONE_NUMBER", "+1234567890")
            customer = Customer(customer_id=data["user_id"], name=f"User {data['user_id']}", phone_number=my_phone, account_balance=1000)
            db.session.add(customer)
            db.session.commit()
            
        otp_code = ''.join(random.choices(string.digits, k=6))
        otp_entry = OTPVerification(
            customer_id=customer.customer_id,
            transaction_id=new_tx.id,
            otp_code=otp_code,
            expires_at=datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
        )
        db.session.add(otp_entry)
        db.session.commit()
        
        sms_msg = f"URGENT: SecurBank detected suspicious activity. Your verification OTP is {otp_code}."
        send_sms(customer.phone_number, sms_msg)

    if decision.alert_required:
        alert_msg = f"Suspicious transaction: Score {decision.score}. Reasons: {', '.join(decision.reasons)}"
        if decision.decision == "STEP_UP" and 'otp_code' in locals():
            alert_msg += f" (Sent OTP: {otp_code})"
            
        new_alert = Alert(
            user_id=data["user_id"],
            event_type="TRANSACTION",
            message=alert_msg
        )
        db.session.add(new_alert)
        # Using Twilio via sms_service.py now for STEP_UP, but also leaving general console hooks
        
    db.session.commit()

    response = {
        "user_id": data["user_id"],
        "risk_score": decision.score,
        "ml_probability": decision.ml_probability,
        "decision": decision.decision,
        "reasons": decision.reasons,
        "action": (
            "Proceed with transaction"
            if decision.decision == "ALLOW"
            else "Require OTP + KYC re-verification"
            if decision.decision == "STEP_UP"
            else "Block request and freeze high-risk actions temporarily"
        ),
        "alert": (
            {
                "send": True,
                "channels": ["sms", "email"],
                "message": f"Suspicious activity detected for user {data['user_id']}.",
            }
            if decision.alert_required
            else {"send": False}
        ),
    }
    return jsonify(response), 200


@app.post("/api/sim-swap/request")
@token_required
def evaluate_sim_swap_request(current_user):
    data = request.get_json(silent=True) or {}
    ok, message = _validate_payload(data)
    if not ok:
        return jsonify({"error": message}), 400

    decision = engine.evaluate(data)

    # Save SIM swap event to DB
    new_event = SimSwapEvent(
        user_id=data["user_id"],
        sim_swap_count_30d=int(data.get("sim_swap_count_30d", 0)),
        hours_since_sim_change=float(data.get("hours_since_sim_change", 9999)),
        risk_score=decision.score,
        decision=decision.decision
    )
    db.session.add(new_event)
    
    if decision.alert_required:
        new_alert = Alert(
            user_id=data["user_id"],
            event_type="SIM_SWAP",
            message=f"Suspicious SIM swap: Score {decision.score}. Reasons: {', '.join(decision.reasons)}"
        )
        db.session.add(new_alert)
        print(f"[*] EXTERNAL HOOK: Sending alert for user {data['user_id']} via SMS/Email...")
        
    db.session.commit()

    status_map = {
        "ALLOW": "approved",
        "STEP_UP": "pending_additional_verification",
        "BLOCK": "rejected",
    }
    return (
        jsonify(
            {
                "user_id": data["user_id"],
                "request_status": status_map[decision.decision],
                "risk_score": decision.score,
                "decision": decision.decision,
                "reasons": decision.reasons,
            }
        ),
        200,
    )

@app.post("/api/customer/verify-otp")
def verify_otp():
    data = request.get_json(silent=True) or {}
    customer_id = data.get("customer_id")
    otp_code = data.get("otp_code")
    
    if not customer_id or not otp_code:
        return jsonify({"error": "Missing customer_id or otp_code"}), 400
        
    verification = OTPVerification.query.filter_by(customer_id=customer_id, otp_code=otp_code, is_verified=False).first()
    
    if not verification:
        return jsonify({"error": "Invalid OTP"}), 400
        
    if verification.expires_at < datetime.datetime.utcnow():
        return jsonify({"error": "OTP expired"}), 400
        
    verification.is_verified = True
    
    tx = Transaction.query.get(verification.transaction_id)
    if tx:
        tx.decision = "ALLOW"
        
    db.session.commit()
    return jsonify({"message": "OTP verified successfully. Transaction approved."}), 200

@app.post("/api/telecom/webhook")
def telecom_webhook():
    # In a real system, we'd verify the X-Telecom-Signature header here
    data = request.get_json(silent=True) or {}
    customer_id = data.get("customer_id")
    
    if not customer_id:
        return jsonify({"error": "Invalid webhook payload"}), 400
        
    payload = {
        "user_id": customer_id,
        "sim_swap_count_30d": 1,
        "hours_since_sim_change": 0.1,
        "new_device": False,
        "location_mismatch": False,
        "failed_logins_24h": 0,
        "transaction_amount": 0
    }
    
    decision = engine.evaluate(payload)
    
    new_event = SimSwapEvent(
        user_id=customer_id,
        sim_swap_count_30d=1,
        hours_since_sim_change=0.1,
        risk_score=decision.score,
        decision=decision.decision
    )
    db.session.add(new_event)
    
    if decision.alert_required:
        new_alert = Alert(
            user_id=customer_id,
            event_type="SIM_SWAP_WEBHOOK",
            message=f"Live Telecom Webhook: SIM swap detected for {customer_id}!"
        )
        db.session.add(new_alert)
        customer = Customer.query.filter_by(customer_id=customer_id).first()
        if customer:
            send_sms(customer.phone_number, f"SECURITY ALERT: Your SIM card was just swapped. If this wasn't you, call us immediately.")
            
    db.session.commit()
    return jsonify({"status": "Webhook received and processed"}), 200



if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
