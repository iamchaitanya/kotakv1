import time
import pyotp
from neo_api_client import NeoAPI
import config

def get_kotak_client():
    """Generates TOTP, logs in, and returns the authenticated NeoAPI client."""
    
    # Generate TOTP
    try:
        totp_generator = pyotp.TOTP(config.TOTP_SECRET)
        auto_totp = totp_generator.now()
        print(f"🤖 Auto-generated TOTP: {auto_totp}")
    except Exception as e:
        print(f"❌ Failed to generate TOTP. Error: {e}")
        return None

    # Authenticate
    try:
        client = NeoAPI(
            environment='prod', 
            access_token=None, 
            neo_fin_key=None, 
            consumer_key=config.CONSUMER_KEY
        )
        
        print("--- Sending Login Request ---")
        client.totp_login(
            mobile_number=config.MOBILE_NUMBER, 
            ucc=config.CLIENT_ID, 
            totp=auto_totp
        )
        
        time.sleep(1) # Brief pause for Kotak's backend
        client.totp_validate(mpin=config.MPIN)
        
        print("✅ 100% Automated Login Successful!")
        return client
        
    except Exception as e:
        print(f"❌ Login Error: {e}")
        return None