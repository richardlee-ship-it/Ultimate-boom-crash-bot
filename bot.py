import pandas as pd
import pandas_ta as ta
import time
import requests
import os

# --- CONFIGURATION (Matches your Railway Variables exactly) ---
TOKEN = os.getenv("BOT_TOKEN") 
CHAT_ID = os.getenv("CHAT_ID")
SYMBOLS = ["Crash 1000 Index", "Boom 1000 Index", "Crash 500 Index", "Boom 500 Index"]

# Storage
candles = {symbol: {'m1': [], 'm5': []} for symbol in SYMBOLS}
last_pre_alert = {symbol: 0 for symbol in SYMBOLS}
bot_activated = False

def send_telegram(message):
    if not TOKEN or not CHAT_ID:
        print(f"Variable Error: BOT_TOKEN is {TOKEN}, CHAT_ID is {CHAT_ID}")
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"Telegram Error: {e}")

def analyze(symbol, latest_price):
    global bot_activated
    
    # Sends a message the VERY SECOND the bot starts receiving data
    if not bot_activated:
        send_telegram("✅ **Bot is now LIVE!**\nRailway variables connected successfully. Collecting first 50 minutes of data now.")
        bot_activated = True

    try:
        m1_list = candles[symbol]['m1']
        m5_list = candles[symbol]['m5']

        # Silence for 50 minutes to ensure math is accurate
        if len(m1_list) < 50 or len(m5_list) < 50:
            return

        m1_df = pd.Series(m1_list)
        m5_df = pd.Series(m5_list)
        
        # Indicator Math
        rsi = ta.rsi(m1_df, length=7).iloc[-1]
        m5_ema50 = ta.ema(m5_df, length=50).iloc[-1]
        m5_ema200 = ta.ema(m5_df, length=200).iloc[-1]
        m1_ema50 = ta.ema(m1_df, length=50).iloc[-1]

        now = time.time()

        # SELL LOGIC (Crash)
        if "Crash" in symbol and m5_ema50 < m5_ema200:
            if 60 <= rsi < 70 and abs(latest_price - m1_ema50) <= 80:
                if now - last_pre_alert[symbol] > 600:
                    send_telegram(f"⚠️ *PRE-SIGNAL: {symbol}*\nApproaching Sell Zone. RSI: {rsi:.2f}")
                    last_pre_alert[symbol] = now
            if rsi >= 70 and abs(latest_price - m1_ema50) <= 50:
                send_telegram(f"🔻 *{symbol} SELL SIGNAL*\nEntry: {latest_price}\nRSI: {rsi:.2f}")

        # BUY LOGIC (Boom)
        elif "Boom" in symbol and m5_ema50 > m5_ema200:
            if 30 < rsi <= 40 and abs(latest_price - m1_ema50) <= 80:
                if now - last_pre_alert[symbol] > 600:
                    send_telegram(f"⚠️ *PRE-SIGNAL: {symbol}*\nApproaching Buy Zone. RSI: {rsi:.2f}")
                    last_pre_alert[symbol] = now
            if rsi <= 30 and abs(latest_price - m1_ema50) <= 50:
                send_telegram(f"🚀 *{symbol} BUY SIGNAL*\nEntry: {latest_price}\nRSI: {rsi:.2f}")

    except Exception:
        pass
