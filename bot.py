import os
import time
import requests

# ==========================================
# 1. FINAL CONFIGURATION (HARD-CODED)
# ==========================================
# This is your NEW token from BotFather
BOT_TOKEN = "8667543667:AAEydSxfo9HcOuNaLuUx0XKOiKNo5t-mON8"

# This is your ID from the User Info Bot
CHAT_ID = "6856488919"

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

def send_telegram_message(message):
    try:
        payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
        response = requests.post(API_URL, json=payload)
        # This will show '200' in your Railway logs if it works!
        print(f"Telegram response: {response.status_code}")
    except Exception as e:
        print(f"Error sending message: {e}")

if __name__ == "__main__":
    print("Bot started. Waiting for market data logic...")
    
    # Send the Live message immediately on startup
    send_telegram_message("✅ *Bot is now LIVE and Connected!* \nReady for Crash/Boom signals.")
    
    while True:
        # The bot stays active here
        time.sleep(60)
