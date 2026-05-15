import os
import time
import requests
import pandas as pd
import pandas_ta as ta

# ==========================================
# 1. CONFIGURATION (BACKUP HARD-CODED)
# ==========================================
# Using the data from your screenshots
HARDCODED_TOKEN = "8667543667:AAEydSxfo9HcOuNaLuUx0XKOiKNo5t-mON8"
HARDCODED_ID = "6856488919"

# This line checks Railway Variables FIRST, then uses the Hard-coded ones if Railway is empty
BOT_TOKEN = os.getenv('BOT_TOKEN', HARDCODED_TOKEN)
CHAT_ID = os.getenv('CHAT_ID', HARDCODED_ID)

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

def send_telegram_message(message):
    try:
        payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
        response = requests.post(API_URL, json=payload)
        # Check logs for '200' (Success) or '401' (Bad Token)
        print(f"Telegram response: {response.status_code}")
        if response.status_code != 200:
            print(f"Error detail: {response.text}")
    except Exception as e:
        print(f"Connection Error: {e}")

# ==========================================
# 2. MARKET LOGIC (CRASH & BOOM)
# ==========================================
def check_signals():
    """
    Placeholder for your calculation logic. 
    It will run every minute after the 50-min warmup.
    """
    pass

if __name__ == "__main__":
    print("--- CONTAINER STARTING ---")
    print(f"Using Chat ID: {CHAT_ID}")
    
    # Send immediate connection test
    send_telegram_message("🚀 *CONNECTION SUCCESSFUL!*\n\nYour bot is now linked to Railway and GitHub correctly. Starting market monitoring...")

    while True:
        # This keeps the bot alive 24/7
        time.sleep(60)
