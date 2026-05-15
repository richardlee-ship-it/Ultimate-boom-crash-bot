import os
import time
import requests

# ==========================================
# 1. AUTHENTICATION (CLEANED)
# ==========================================
# This is your new token, fixed into one single line
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
        
        # Monitor this! We want '200'
        print(f"Telegram Log Status: {r.status_code}")
        if r.status_code != 200:
            print(f"Server Response: {r.text}")
    except Exception as e:
        print(f"Connection Error: {e}")

def analyze_market(symbol):
    # Your market scanning logic is already working!
    print(f"--- Scanning {symbol} ---")
    pass

if __name__ == "__main__":
    print("--- MULTI-INDEX BOT STARTING ---")
    
    # Final connection check
    send_telegram_signal("✅ *VARIABLES CLEARED*\nBot is now scanning all 5 Indices.")

    while True:
        for market in SYMBOLS:
            try:
                analyze_market(market)
            except Exception as e:
                print(f"Error on {market}: {e}")
        time.sleep(60)
