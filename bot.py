import pandas as pd
import pandas_ta as ta
import time
import requests
import os

# --- CONFIGURATION ---
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"
SYMBOLS = ["Crash 1000 Index", "Boom 1000 Index", "Crash 500 Index", "Boom 500 Index"]

# Dictionary to store candle data
# We need at least 200 candles to calculate EMA 200 accurately
candles = {symbol: {'m1': [], 'm5': []} for symbol in SYMBOLS}
last_pre_alert_time = {symbol: 0 for symbol in SYMBOLS} # To avoid spamming alerts

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}&parse_mode=Markdown"
    try:
        requests.get(url)
    except Exception as e:
        print(f"Error sending Telegram: {e}")

def near_ema(price, ema_value, threshold=50):
    return abs(price - ema_value) <= threshold

def analyze(symbol, latest_price):
    m1_list = candles[symbol]['m1']
    m5_list = candles[symbol]['m5']

    # 1. Data Check (Need 200 for EMA 200)
    if len(m1_list) < 200 or len(m5_list) < 200:
        if int(time.time()) % 60 == 0:
            print(f"DEBUG {symbol}: Syncing... M1: {len(m1_list)}/200, M5: {len(m5_list)}/200")
        return

    # 2. Indicators
    m1_df = pd.Series(m1_list)
    m5_df = pd.Series(m5_list)
    
    latest_rsi = ta.rsi(m1_df, length=7).iloc[-1]
    m5_ema50 = ta.ema(m5_df, length=50).iloc[-1]
    m5_ema200 = ta.ema(m5_df, length=200).iloc[-1]
    m1_ema50 = ta.ema(m1_df, length=50).iloc[-1]

    current_time = time.time()
    
    # --- CRASH LOGIC (SELLS) ---
    if m5_ema50 < m5_ema200: # Bearish Trend
        # PRE-ALERT: RSI climbing and near EMA
        if 60 <= latest_rsi < 70 and near_ema(latest_price, m1_ema50, 80):
            if current_time - last_pre_alert_time[symbol] > 300: # Only alert once every 5 mins
                send_telegram(f"⚠️ *PRE-SIGNAL: {symbol}*\nPrice is approaching the Sell Zone! RSI is {latest_rsi:.2f}. Watch for a crash soon.")
                last_pre_alert_time[symbol] = current_time

        # FINAL SIGNAL
        if latest_rsi >= 70 and near_ema(latest_price, m1_ema50, 50):
            msg = (f"🔻 *CRASH 1000 SELL SIGNAL*\n"
                   f"Entry: {latest_price}\n"
                   f"RSI: {latest_rsi:.2f}\n"
                   f"Trend: Bearish ✅")
            send_telegram(msg)
            print(f"!!! SIGNAL SENT FOR {symbol} !!!")

    # --- BOOM LOGIC (BUYS) ---
    elif m5_ema50 > m5_ema200: # Bullish Trend
        # PRE-ALERT: RSI dropping and near EMA
        if 30 < latest_rsi <= 40 and near_ema(latest_price, m1_ema50, 80):
            if current_time - last_pre_alert_time[symbol] > 300:
                send_telegram(f"⚠️ *PRE-SIGNAL: {symbol}*\nPrice is approaching the Buy Zone! RSI is {latest_rsi:.2f}. Watch for a spike soon.")
                last_pre_alert_time[symbol] = current_time

        # FINAL SIGNAL
        if latest_rsi <= 30 and near_ema(latest_price, m1_ema50, 50):
            msg = (f"🚀 *BOOM 1000 BUY SIGNAL*\n"
                   f"Entry: {latest_price}\n"
                   f"RSI: {latest_rsi:.2f}\n"
                   f"Trend: Bullish ✅")
            send_telegram(msg)
            print(f"!!! SIGNAL SENT FOR {symbol} !!!")

# --- PLACEHOLDER FOR YOUR BROKER CONNECTION ---
# This part depends on if you use Deriv API or a library like MetaTrader5
# You must feed 'candles[symbol]['m1']' and 'm5' with closing prices.
