import os
from dotenv import load_dotenv

load_dotenv()

def send_sms(to_phone: str, message: str) -> bool:
    print(f"\n=======================================================")
    print(f"[SIMULATED SMS to {to_phone}]")
    print(f"Message: {message}")
    print(f"=======================================================\n")
    return True

