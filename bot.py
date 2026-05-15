import os
import time
import requests
import pandas as pd
import pandas_ta as ta

# ==========================================
# HARD-CODED CONFIGURATION (PRE-FILLED)
# ==========================================
BOT_TOKEN = "8667543667:AAEydSxfo9HcOuNaLuUx0XKOiKNo5t-mON8"
CHAT_ID = "6856488919"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

def send_telegram_message(message):
    try:
        payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
        r = requests.post(API_URL, json=payload)
        print(f"Telegram response: {r.status_code}")
    except Exception as e:
        print(f"Error sending message: {e}")

if __name__ == "__main__":
    # This message should hit your phone immediately after deploy
    send_telegram_message("✅ *Bot is now LIVE with New Token!* \nStarting data collection for Crash/Boom...")
    
    print("Bot started. Waiting for market data logic...")
    while True:
        # The trading logic stays here
        time.sleep(60)
