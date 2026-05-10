# SIM Swap Detection & Prevention (50% Build)

This is a **mid-project implementation** of the system described in `SAMM.pdf`.
It is intentionally scoped to about 50% completion so you can demonstrate progress.

## What is implemented

- Flask backend service
- Synthetic-data ML model (Logistic Regression) for fraud probability
- Rule + ML hybrid risk scoring engine
- Decision outcomes:
  - `ALLOW` (low risk)
  - `STEP_UP` (medium risk, needs extra verification)
  - `BLOCK` (high risk)
- Alert payload generation for suspicious events
- REST APIs to:
  - Evaluate login/transaction risk
  - Evaluate SIM swap request risk
- Quick local guide to run and show the prototype

## What is intentionally pending (next 50%)

- Real database integration (currently in-memory/demo mode)
- Real telecom/bank data pipeline
- User account management + authentication
- Real SMS/Email gateway integration
- Frontend dashboard
- Continuous model retraining with production data

## Project structure

- `app.py` - Flask API entry point
- `risk_engine.py` - Rule + ML scoring logic
- `train_model.py` - Synthetic-data model trainer/loader
- `requirements.txt` - Python dependencies

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Server starts at: `http://127.0.0.1:5000`

## Demo API calls

### 1) Health check

```bash
curl http://127.0.0.1:5000/health
```

### 2) SIM swap risk evaluation

```bash
curl -X POST http://127.0.0.1:5000/api/sim-swap/request ^
  -H "Content-Type: application/json" ^
  -d "{\"user_id\":\"U1001\",\"sim_swap_count_30d\":2,\"hours_since_sim_change\":1,\"new_device\":true,\"location_mismatch\":true,\"failed_logins_24h\":5,\"transaction_amount\":75000}"
```

### 3) Login/transaction event evaluation

```bash
curl -X POST http://127.0.0.1:5000/api/risk/evaluate ^
  -H "Content-Type: application/json" ^
  -d "{\"user_id\":\"U1002\",\"sim_swap_count_30d\":0,\"hours_since_sim_change\":120,\"new_device\":false,\"location_mismatch\":false,\"failed_logins_24h\":0,\"transaction_amount\":2000}"
```

## Guide-ready talking points

Use these to present your 50% progress:

1. We implemented core fraud detection logic using ML + behavior rules.
2. We can classify requests in real time into allow/step-up/block.
3. We added prevention hooks (blocking and alert payloads).
4. Next, we will integrate live banking/telecom systems and a dashboard UI.
