import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from telethon import TelegramClient, events
from dotenv import load_dotenv

# Import your existing Kotak and Strategy modules
from auth import get_kotak_client
from market_data import fetch_scrip_master, get_nearest_sensex_options
from strategy.parser import parse_telegram_signal

# Load Environment Variables
load_dotenv()
API_ID = int(os.getenv("TG_API_ID"))
API_HASH = os.getenv("TG_API_HASH")
TARGET_CHAT = int(os.getenv("TG_TARGET_CHAT"))

# --- TRADE SETTINGS (Controlled via Frontend) ---
class TradeSettings(BaseModel):
    lots: int = 1                     # Default: 1 lot
    product_type: str = "MIS"         # MIS (Intraday) or NRML (Overnight)
    order_type: str = "L"             # L (Limit) or MKT (Market)
    price_mode: str = "LOW"           # 'LOW' or 'HIGH'
    is_trading_active: bool = False   # Master Kill Switch

# --- GLOBAL STATE ---
tg_client = TelegramClient('anon', API_ID, API_HASH)
KOTAK_CLIENT = None
SENSEX_DF = None
CURRENT_SETTINGS = TradeSettings()
trade_queue = asyncio.Queue()

def setup_kotak_data():
    """Attempts to log into Kotak and fetch the Master Data (Lazy Load)"""
    global KOTAK_CLIENT, SENSEX_DF
    print("🔐 Attempting Kotak Neo Login...")
    client = get_kotak_client()
    
    if not client:
        print("⚠️ Kotak login failed. Dashboard will run, but trading is offline.")
        return False
        
    print("📥 Downloading BSE Master Data...")
    raw_bse = fetch_scrip_master(client, segment="bse_fo.csv")
    
    # --- SAFETY CHECK ---
    if raw_bse is None or raw_bse.empty:
        print("⚠️ Failed to download BSE Master (Kotak didn't provide it). Trading offline.")
        return False
        
    df = get_nearest_sensex_options(raw_bse)
    
    if df is not None and not df.empty:
        KOTAK_CLIENT = client
        SENSEX_DF = df
        print(f"✅ Master loaded! Ready to trade {len(SENSEX_DF)} Sensex contracts.")
        return True
    else:
        print("⚠️ Failed to parse Sensex options. Trading offline.")
        return False

async def trade_worker():
    """Background task that watches the queue and executes trades."""
    print("⚙️ Trade worker started, waiting for signals...")
    while True:
        try:
            signal = await trade_queue.get()
            
            if not CURRENT_SETTINGS.is_trading_active:
                print("🛑 Trading is currently DISABLED via frontend. Skipping signal.")
                trade_queue.task_done()
                continue
                
            if not KOTAK_CLIENT or SENSEX_DF is None:
                print("❌ Cannot execute: Kotak client is offline or Master Data is missing.")
                trade_queue.task_done()
                continue

            print(f"\n🚀 EXECUTING TRADE: {signal['strike']} {signal['type']}")
            
            match = SENSEX_DF[
                (SENSEX_DF['pStrike'] == float(signal['strike'])) & 
                (SENSEX_DF['pOptionType'] == signal['type'])
            ]
            
            if match.empty:
                print(f"❌ Error: Could not find token for {signal['strike']} {signal['type']} in Master Data.")
                trade_queue.task_done()
                continue
                
            token = str(match.iloc[0]['pSymbol'])
            lot_size = int(match.iloc[0]['pMultiplier'])
            
            total_qty = lot_size * CURRENT_SETTINGS.lots
            target_price = signal['low'] if CURRENT_SETTINGS.price_mode == "LOW" else signal['high']
            
            if CURRENT_SETTINGS.order_type == "MKT":
                target_price = 0

            print(f"🛒 Sending Order -> Token: {token} | Qty: {total_qty} ({CURRENT_SETTINGS.lots} lots) | Price: {target_price} | Type: {CURRENT_SETTINGS.order_type}")

            """
            response = KOTAK_CLIENT.place_order(
                exchange_segment="bfo",
                product=CURRENT_SETTINGS.product_type,
                price=str(target_price),
                order_type=CURRENT_SETTINGS.order_type,
                quantity=str(total_qty),
                validity="DAY",
                transaction_type="B",
                instrument_token=token
            )
            print(f"✅ Kotak Response: {response}")
            """
            
            trade_queue.task_done()
            
        except asyncio.CancelledError:
            print("🛑 Trade worker cancelled.")
            break
        except Exception as e:
            print(f"❌ Error executing trade: {e}")
            trade_queue.task_done()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting unified engine...")
    setup_kotak_data()
    await tg_client.start()
    print(f"🎧 Telegram connected and listening to chat: {TARGET_CHAT}")
    
    worker_task = asyncio.create_task(trade_worker())
    yield
    print("🛑 Shutting down. Disconnecting Telegram and Workers...")
    worker_task.cancel()
    await tg_client.disconnect()

app = FastAPI(title="Kotak Trading Bot & API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@tg_client.on(events.NewMessage(chats=TARGET_CHAT))
async def incoming_message_handler(event):
    message_text = event.message.message
    signal = parse_telegram_signal(message_text)
    
    if signal['status'] == 'ignored' or signal['status'] == 'empty':
        return
        
    print(f"🎯 VALID SIGNAL RECEIVED: {signal['strike']} {signal['type']} @ {signal['low']}-{signal['high']}")
    await trade_queue.put(signal)

@app.get("/api/settings")
def get_settings():
    return {"status": "success", "data": CURRENT_SETTINGS.dict()}

@app.post("/api/settings")
def update_settings(new_settings: TradeSettings):
    global CURRENT_SETTINGS
    CURRENT_SETTINGS = new_settings
    print(f"⚙️ Settings Updated via API: {CURRENT_SETTINGS.dict()}")
    return {"status": "success", "message": "Trade settings updated successfully."}

@app.post("/api/retry-kotak-login")
def retry_login():
    if setup_kotak_data():
        return {"status": "success", "message": "Kotak logged in successfully!"}
    raise HTTPException(status_code=500, detail="Kotak login failed.")

@app.post("/api/emergency-stop")
def emergency_stop():
    global CURRENT_SETTINGS
    CURRENT_SETTINGS.is_trading_active = False
    print("🚨 PANIC BUTTON HIT: Trading is now DISABLED.")
    
    cleared_count = 0
    while not trade_queue.empty():
        try:
            trade_queue.get_nowait()
            trade_queue.task_done()
            cleared_count += 1
        except asyncio.QueueEmpty:
            break
            
    print(f"🗑️ Queue flushed. Deleted {cleared_count} pending signals.")
    
    if KOTAK_CLIENT:
        print("⏳ (Implementation Pending) Cancelling all open orders at broker...")
        
    return {
        "status": "success", 
        "message": f"EMERGENCY STOP ACTIVATED. {cleared_count} pending trades deleted."
    }

@app.get("/api/sensex-options")
def get_sensex_options():
    if SENSEX_DF is None or SENSEX_DF.empty:
        return {"status": "success", "data": []}
    return {"status": "success", "data": SENSEX_DF.head(20).to_dict(orient="records")}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("unified_main:app", host="0.0.0.0", port=8000, reload=True, ws="none")