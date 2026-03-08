import os
import time
import pyotp
from dotenv import load_dotenv
from neo_api_client import NeoAPI

# Load the variables from your .env file
load_dotenv()

CONSUMER_KEY = os.getenv("KOTAK_CONSUMER_KEY")
MOBILE_NUMBER = os.getenv("KOTAK_MOBILE_NUMBER")
CLIENT_ID = os.getenv("KOTAK_CLIENT_ID")
MPIN = os.getenv("KOTAK_MPIN")
TOTP_SECRET = os.getenv("KOTAK_TOTP_SECRET")

# Automatically generate the live 6-digit TOTP
# pyotp creates the exact same code your Google Authenticator does
try:
    totp_generator = pyotp.TOTP(TOTP_SECRET)
    auto_totp = totp_generator.now()
    print(f"🤖 Auto-generated TOTP: {auto_totp}")
except Exception as e:
    print(f"❌ Failed to generate TOTP. Check your secret key in .env. Error: {e}")
    exit()

try:
    # 1. Initialize Client
    client = NeoAPI(
        environment='prod', 
        access_token=None, 
        neo_fin_key=None, 
        consumer_key=CONSUMER_KEY
    )

    # 2. Automated TOTP Login
    print("--- Sending Login Request ---")
    client.totp_login(
        mobile_number=MOBILE_NUMBER, 
        ucc=CLIENT_ID, 
        totp=auto_totp  # Passing the auto-generated code here!
    )

    # 3. MPIN Validation
    # We add a tiny 1-second delay to ensure Kotak's servers process step 2 first
    time.sleep(1) 
    client.totp_validate(mpin=MPIN)

    print("\n✅ 100% Automated Login Successful! You are connected.")

    # 4. Fetch Account Limits to verify
    limits = client.limits()
    if limits.get('stat') == 'Ok':
         print("Account Data Fetched Successfully.")

except Exception as e:
    print(f"\n❌ An error occurred: {e}")