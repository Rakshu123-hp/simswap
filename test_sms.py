from sms_service import send_sms
import os
from dotenv import load_dotenv

load_dotenv()
my_number = os.getenv("MY_PHONE_NUMBER")

if my_number:
    print(f"Attempting to send test SMS to {my_number}...")
    success = send_sms(my_number, "Test SMS from Fraud Risk Engine!")
    if success:
        print("Test script finished successfully.")
    else:
        print("Test script failed.")
else:
    print("MY_PHONE_NUMBER is not set in .env")
