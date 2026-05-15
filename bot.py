import os
import time
import requests

# This looks for the names you created in the Railway dashboard
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

SYMBOLS = [
    "Crash 1000 Index", 
    "Boom 1000 Index", 
    "Crash 900 Index", 
    "Crash 500 Index", 
    "Boom 500 Index"
]

def send_telegram_signal(message):
    if not TOKEN or not CHAT_ID:
        print("❌ ERROR: Missing variables in Railway Dashboard!")
        return

    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        r = requests.post(url, json=payload)
        
        print(f"Telegram Status: {r.status_code}")
        if r.status_code != 200:
            print(f"Server Response: {r.text}")
            
    except Exception as e:
        print(f"Connection Error: {e}")

if __name__ == "__main__":
    print("--- MULTI-INDEX BOT ACTIVE ---")
    
    # This will prove if the variables are working
    send_telegram_signal("🤖 *Sync Successful!*\nBot is reading from Railway variables.")

    while True:
        # This is the loop you see working in your logs
        for market in SYMBOLS:
            print(f"--- Scanning {market} ---")
            
        # Wait 1 minute before next scan
        time.sleep(60)
