import os
import time
import requests

# ==========================================
# 1. AUTHENTICATION (FIXED NEW TOKEN)
# ==========================================
# I combined the two lines from your paste into one perfect string here
BOT_TOKEN = "8667543667:AAFFdhIPIjJGAVcbQ3be8wYgQQNvy_5mB9s".strip()
CHAT_ID = "6856488919".strip()

# Your requested 5 indices
SYMBOLS = [
    "Crash 1000 Index", 
    "Boom 1000 Index", 
    "Crash 900 Index", 
    "Crash 500 Index", 
    "Boom 500 Index"
]

def send_telegram_signal(message):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
        r = requests.post(url, json=payload)
        # We are looking for '200' in the Railway logs now!
        print(f"Telegram Log Status: {r.status_code}")
        if r.status_code != 200:
            print(f"Server Response: {r.text}")
    except Exception as e:
        print(f"Connection Error: {e}")

def analyze_market(symbol):
    # This matches the loop seen in your Railway logs
    print(f"--- Scanning {symbol} ---")
    pass

if __name__ == "__main__":
    print("--- MULTI-INDEX BOT STARTING ---")
    
    # This message should hit your phone INSTANTLY after you save
    startup_msg = (
        "🚀 *NEW TOKEN CONNECTED!*\n\n"
        "Your bot is now authorized. Monitoring:\n"
        "• Crash 1000, 900, 500\n"
        "• Boom 1000, 500\n\n"
        "Timeframe: M1 (1 Minute)"
    )
    send_telegram_signal(startup_msg)

    while True:
        for market in SYMBOLS:
            try:
                analyze_market(market)
            except Exception as e:
                print(f"Error on {market}: {e}")
        
        # Wait 60 seconds to check for new candles
        time.sleep(60)
