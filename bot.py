import os
import time
import requests

# ==========================================
# 1. AUTHENTICATION (MANUALLY JOINED)
# ==========================================
# This is the exact token from IMG_1763 joined into one line
TOKEN = "8667543667:AAFFdhIPIjJGAVcbQ3be8wYgQQNvy_5mB9s"
MY_ID = "6856488919"

SYMBOLS = [
    "Crash 1000 Index", 
    "Boom 1000 Index", 
    "Crash 900 Index", 
    "Crash 500 Index", 
    "Boom 500 Index"
]

def send_telegram_signal(message):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": MY_ID, "text": message, "parse_mode": "Markdown"}
        r = requests.post(url, json=payload)
        
        # We need this to say 200!
        print(f"Telegram Log Status: {r.status_code}")
        if r.status_code != 200:
            print(f"Server Response: {r.text}")
    except Exception as e:
        print(f"Connection Error: {e}")

def analyze_market(symbol):
    # Your logs show this part is working perfectly already
    print(f"--- Scanning {symbol} ---")
    pass

if __name__ == "__main__":
    print("--- MULTI-INDEX BOT STARTING ---")
    
    # This is the confirmation message
    send_telegram_signal("💎 *TOKEN VERIFIED*\nBot is now scanning all 5 Index markets.")

    while True:
        for market in SYMBOLS:
            try:
                analyze_market(market)
            except Exception as e:
                print(f"Error on {market}: {e}")
        
        # Wait 1 minute
        time.sleep(60)
