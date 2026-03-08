import os
from dotenv import load_dotenv

# Load the variables from your .env file
load_dotenv()

CONSUMER_KEY = os.getenv("KOTAK_CONSUMER_KEY")
MOBILE_NUMBER = os.getenv("KOTAK_MOBILE_NUMBER")
CLIENT_ID = os.getenv("KOTAK_CLIENT_ID")
MPIN = os.getenv("KOTAK_MPIN")
TOTP_SECRET = os.getenv("KOTAK_TOTP_SECRET")