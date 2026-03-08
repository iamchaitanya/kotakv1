import os
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient, events

# Import our custom modules!
from auth import get_kotak_client
from market_data import fetch_scrip_master, get_nearest_sensex_options
from strategy.parser import parse_telegram_signal

# Load Environment Variables
load_dotenv()
API_ID = int(os.getenv("TG_API_ID"))
API_HASH = os.getenv("TG_API_HASH")
TARGET_CHAT = int(os.getenv("TG_TARGET_CHAT"))

# Initialize Telegram
tg_client = TelegramClient('anon', API_ID, API_HASH)

# Global variable to hold our Kotak Dataframe
SENSEX_DF = None

def setup_kotak_data():
    """Logs into Kotak and downloads today's active Sensex options."""
    global SENSEX_DF
    print("🔐 Logging into Kotak Neo...")
    kotak_client = get_kotak_client()
    
    if not kotak_client:
        print("❌ Kotak login failed. Exiting.")
        return False
        
    print("📥 Downloading BSE Master Data...")
    raw_bse = fetch_scrip_master(kotak_client, segment="bse_fo.csv")
    SENSEX_DF = get_nearest_sensex_options(raw_bse)
    
    if SENSEX_DF is not None and not SENSEX_DF.empty:
        print(f"✅ Master loaded! Ready to trade {len(SENSEX_DF)} Sensex contracts.")
        return True
    else:
        print("❌ Failed to parse Sensex options.")
        return False

def get_instrument_token(strike, opt_type):
    """Finds the Kotak Token for the parsed strike & type."""
    if SENSEX_DF is None:
        return None
        
    match = SENSEX_DF[(SENSEX_DF['dStrikePrice'] == strike) & (SENSEX_DF['pOptionType'] == opt_type)]
    
    if not match.empty:
        return match.iloc[0]['pSymbol'] # The magic Kotak Token!
    return None

# --- TELEGRAM EVENT LISTENER ---
@tg_client.on(events.NewMessage(chats=TARGET_CHAT))
async def incoming_message_handler(event):
    message_text = event.message.message
    print(f"\n📩 NEW MESSAGE RECEIVED:\n{message_text}\n")
    
    # 1. Run it through your exact JavaScript logic (translated to Python)
    signal = parse_telegram_signal(message_text)
    
    if signal['status'] == 'ignored':
        print(f"⏭️ IGNORED: {signal['reason']}")
        return
    elif signal['status'] == 'empty':
        return
        
    # 2. Valid Signal! Find the Token
    print(f"🎯 VALID SIGNAL DETECTED: {signal['index']} {signal['strike']} {signal['type']} at {signal['low']}-{signal['high']}")
    
    token = get_instrument_token(signal['strike'], signal['type'])
    
    if token:
        print(f"✅ FOUND KOTAK TOKEN: {token}")
        print("🚀 -> READY TO TRIGGER ORDER_MANAGER <- 🚀")
        # TODO: orders.place_trade(token, signal['low'])
    else:
        print(f"❌ ERROR: Token not found in today's Master for {signal['strike']} {signal['type']}")

async def main():
    # Setup Kotak First
    if not setup_kotak_data():
        return
        
    # Start listening to Telegram
    print(f"🎧 Listening to chat ID: {TARGET_CHAT} for signals...")
    await tg_client.start()
    await tg_client.run_until_disconnected()

if __name__ == '__main__':
    # Run the async loop
    asyncio.run(main())