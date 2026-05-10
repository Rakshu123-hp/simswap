# SecurBank Fraud Analytics System

A production-ready microservice and live dashboard designed to detect and prevent **SIM Swap Fraud** in real-time. This system uses a hybrid Risk Engine (Machine Learning + Heuristic Rules) to evaluate transactions, combined with a secure "Step-Up" OTP flow to intercept threats without locking out legitimate customers.

## 🚀 Features

*   **Hybrid Risk Engine:** Evaluates transactions based on new device fingerprints, location mismatches, and time since last SIM swap.
*   **Live Analyst Dashboard:** A modern, auto-refreshing UI for bank employees to monitor live threats and take action.
*   **Step-Up Verification (OTP):** Automatically halts suspicious transactions and sends a 6-digit OTP to the user's registered phone number to confirm identity.
*   **Telecom Webhook Integration:** Dedicated REST endpoint for ingesting live alerts directly from telecom providers.
*   **SQLite Ledger:** Full relational database for tracking users, transactions, and secure OTP tokens.

---

## 🛠️ Step-by-Step Setup Guide

Follow these instructions to run the project from scratch on your local machine.

### Prerequisites
*   Python 3.10 or higher installed.
*   Git (optional, to clone the repository).

### Step 1: Extract / Clone the Project
Unzip the project files into a folder, or clone the repository to your local machine. Open your terminal or command prompt and navigate (`cd`) into the project folder.

### Step 2: Create a Virtual Environment
It is highly recommended to isolate the project dependencies.
```bash
# Windows
python -m venv .venv
.\.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies
Install all required libraries, including Flask, SQLAlchemy, Scikit-Learn, and others.
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Create a file named `.env` in the root folder of the project. Add the following line to it:
```ini
MY_PHONE_NUMBER=+1234567890
```
*(You can put your real phone number here, but ensure it includes the country code, e.g., +91 for India, +1 for US).*

### Step 5: Start the Backend Server
Run the Flask application. This will automatically create the `instance/sim_swap.db` database and train the machine learning model on the first startup.
```bash
python app.py
```
*The server will start running at `http://127.0.0.1:5000`.*

### Step 6: Start the Live Traffic Simulator
To see the dashboard light up with real data, open a **second terminal window**, activate your virtual environment again, and run the simulator:
```bash
# Windows
.\.venv\Scripts\activate
python traffic_simulator.py

# macOS / Linux
source .venv/bin/activate
python traffic_simulator.py
```

### Step 7: View the Dashboard
1. Open your web browser and go to: `http://127.0.0.1:5000/dashboard`
2. You will see the beautiful glassmorphism login screen.
3. Click **"SECURE LOGIN"** (Any username/password works for this presentation demo).
4. Watch the live transactions roll in!

---

## 🐳 Docker Setup (Alternative)

If you have Docker installed, running the project is even easier! You don't need to install Python or set up a virtual environment.

1. Ensure Docker Desktop is running.
2. In your terminal, run:
```bash
docker-compose up --build
```
3. Open `http://127.0.0.1:5000/dashboard` in your browser.

---

## 🧪 How to Demo the "Step-Up" OTP Flow

1. Leave the **Traffic Simulator** running in the background.
2. Look at the dashboard's **Recent Alerts** table on the left side.
3. Wait for a transaction to get flagged as **STEP_UP** (Yellow Badge).
4. The system will simulate sending an SMS. Read the end of the alert message on your screen: e.g., `(Sent OTP: 582910)`.
5. Click the floating blue **"📱 Simulate Customer OTP"** button in the bottom right corner of the dashboard.
6. Enter the **User ID** exactly as it appears in the table (e.g., `U-4912`).
7. Enter the **6-Digit OTP** you just read from the alert.
8. Click **Submit**. The dashboard will instantly update, and the locked transaction will turn green (`ALLOW`)!
