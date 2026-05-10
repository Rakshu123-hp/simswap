import time
import random
import urllib.request
import json

BASE_URL = "http://127.0.0.1:5000"
TOKEN = None

def get_token():
    # Auto-register and login to get a token
    data = json.dumps({"username": "simulator_bot", "password": "bot_password"}).encode('utf-8')
    req = urllib.request.Request(f"{BASE_URL}/api/auth/register", data=data, headers={'Content-Type': 'application/json'})
    try:
        urllib.request.urlopen(req)
    except Exception:
        pass # Already registered
        
    req = urllib.request.Request(f"{BASE_URL}/api/auth/login", data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read())
            return res_data['token']
    except Exception as e:
        print(f"Failed to get token: {e}")
        return None

def send_event(endpoint, payload, token):
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(f"{BASE_URL}{endpoint}", data=data, headers={
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    })
    try:
        urllib.request.urlopen(req)
        print(f"Sent event to {endpoint}")
    except Exception as e:
        print(f"Error sending event: {e}")

def simulate():
    global TOKEN
    TOKEN = get_token()
    if not TOKEN:
        print("Waiting for server to start...")
        time.sleep(5)
        return
        
    print("Traffic Simulator Started. Press Ctrl+C to stop.")
    
    while True:
        # Determine event type
        event_type = random.choices(
            ['NORMAL_TX', 'STEP_UP_TX', 'FRAUD_TX', 'NORMAL_SIM', 'SUSPICIOUS_SIM'],
            weights=[50, 20, 10, 15, 5], k=1
        )[0]
        
        user_id = f"U-{random.randint(1000, 9999)}"
        
        if event_type == 'NORMAL_TX':
            payload = {
                "user_id": user_id, "sim_swap_count_30d": 0, "hours_since_sim_change": random.randint(100, 500),
                "new_device": False, "location_mismatch": False, "failed_logins_24h": 0, "transaction_amount": random.randint(10, 500)
            }
            send_event("/api/risk/evaluate", payload, TOKEN)
            
        elif event_type == 'STEP_UP_TX':
            # This generates a score of around 37-50, which falls perfectly into STEP_UP (35-64)
            payload = {
                "user_id": user_id, "sim_swap_count_30d": 0, "hours_since_sim_change": random.randint(1, 23),
                "new_device": True, "location_mismatch": False, "failed_logins_24h": 0, "transaction_amount": random.randint(10, 500)
            }
            send_event("/api/risk/evaluate", payload, TOKEN)
            
        elif event_type == 'FRAUD_TX':
            payload = {
                "user_id": user_id, "sim_swap_count_30d": random.randint(1, 3), "hours_since_sim_change": random.randint(1, 24),
                "new_device": True, "location_mismatch": True, "failed_logins_24h": random.randint(3, 8), "transaction_amount": random.randint(10000, 90000)
            }
            send_event("/api/risk/evaluate", payload, TOKEN)
            
        elif event_type == 'NORMAL_SIM':
            payload = {
                "user_id": user_id, "sim_swap_count_30d": 0, "hours_since_sim_change": 9999,
                "new_device": False, "location_mismatch": False, "failed_logins_24h": 0, "transaction_amount": 0
            }
            send_event("/api/sim-swap/request", payload, TOKEN)
            
        elif event_type == 'SUSPICIOUS_SIM':
            payload = {
                "user_id": user_id, "sim_swap_count_30d": random.randint(1, 2), "hours_since_sim_change": 1,
                "new_device": True, "location_mismatch": True, "failed_logins_24h": random.randint(1, 4), "transaction_amount": 0
            }
            send_event("/api/sim-swap/request", payload, TOKEN)
            
        # Wait a random amount of time between 2 and 7 seconds
        time.sleep(random.uniform(2.0, 7.0))

if __name__ == "__main__":
    while True:
        try:
            simulate()
        except KeyboardInterrupt:
            break
        except Exception:
            time.sleep(5)
