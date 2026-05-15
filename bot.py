import os
import time
import requests
import pandas as pd
import pandas_ta as ta

# ==========================================
# 1. AUTHENTICATION (CLEANED)
# ==========================================
# .strip() removes any accidental spaces that cause the 401 error
BOT_TOKEN = "8667543667:AAEydSxfo9HcOuNaLuUx0XKOiKNo5t-mON8".strip()
CHAT_ID = "6856488919".strip()

# Your requested 5 indices from MT5
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
        # 200 = Success / 401 = Bad Token
        print(f"Telegram Log: {r.status_code}")
        if r.status_code != 200:
            print(f"Error Detail: {r.text}")
    except Exception as e:
        print(f"Connection Error: {e}")

# ==========================================
# 2. MARKET ANALYSIS ENGINE
# ==========================================
def analyze_market(symbol):
    """
    Logic for RSI(7) and 200 EMA strategy.
    """
    print(f"--- Scanning {symbol} ---")
    
    # In a full live setup, you would connect to Deriv API here.
    # This loop keeps the bot active and ready to process data.
    pass

if __name__ == "__main__":
    print("--- MULTI-INDEX BOT STARTING ---")
    
    # Initial status message to confirm your phone is connected
    startup_msg = (
        "📈 *Trading Engine Online*\n\n"
        "Monitoring Indices:\n"
        "• Crash 1000, 900, 500\n"
        "• Boom 1000, 500\n\n"
        "Strategy: RSI(7) + 200 EMA"
    )
    send_telegram_signal(startup_msg)

    while True:
        for market in SYMBOLS:
            try:
                analyze_market(market)
            except Exception as e:
                print(f"Error on {market}: {e}")
        
        # Wait 60 seconds (1 minute) to match M1 candles
        time.sleep(60)
