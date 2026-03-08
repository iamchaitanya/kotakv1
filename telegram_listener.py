import os
from dotenv import load_dotenv
from telethon.sync import TelegramClient

# Load variables
load_dotenv()
API_ID = int(os.getenv("TG_API_ID"))
API_HASH = os.getenv("TG_API_HASH")
PHONE = os.getenv("TG_PHONE_NUMBER")

# 1. Initialize the Telegram Client
# 'anon' is the name of the session file it will create to remember your login
client = TelegramClient('anon', API_ID, API_HASH)

async def main():
    print("🤖 Connecting to Telegram...")
    
    # 2. Get the 15 most recent chats/groups you are in
    dialogs = await client.get_dialogs(limit=15)
    
    print("\n--- YOUR RECENT TELEGRAM CHATS ---")
    print(f"{'CHAT NAME':<40} | {'CHAT ID'}")
    print("-" * 65)
    
    for dialog in dialogs:
        # We use repr() to safely print names with emojis
        print(f"{repr(dialog.name)[:38]:<40} | {dialog.id}")
        
    print("-" * 65)
    print("👉 Find your Trading Group in the list above and copy its CHAT ID (usually starts with -100).")

# Run the client
with client:
    client.loop.run_until_complete(main())