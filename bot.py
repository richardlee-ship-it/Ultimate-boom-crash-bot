import pandas as pd
import pandas_ta as ta
import time
import requests

# --- CONFIGURATION ---
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"
SYMBOLS = ["Crash 1000 Index", "Boom 1000 Index", "Crash 500 Index", "Boom 500 Index"]

# Storage
candles = {symbol: {'m1': [], 'm5': []} for symbol in SYMBOLS}
last_pre_alert = {symbol: 0 for symbol in SYMBOLS}
has_sent_start_msg = False

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"Telegram Error: {e}")

def analyze(symbol, latest_price):
    global has_sent_start_msg
    
    # Send a one-time message when the first tick arrives
    if not has_sent_start_msg:
        send_telegram("🤖 *Bot Started Successfully!*\nCollecting initial market data... please wait.")
        has_sent_start_msg = True

    try:
        m1_list = candles[symbol]['m1']
        m5_list = candles[symbol]['m5']

        # FAST START: Reduced from 200 to 50
        if len(m1_list) < 50 or len(m5_list) < 50:
            if int(time.time()) % 60 == 0:
                print(f"Syncing {symbol}: M1({len(m1_list)}/50) M5({len(m5_list)}/50)")
            return

        m1_df = pd.Series(m1_list)
        m5_df = pd.Series(m5_list)
        
        # Calculations
        rsi_series = ta.rsi(m1_df, length=7)
        ema50_series = ta.ema(m5_df, length=50)
        ema200_series = ta.ema(m5_df, length=200)
        m1_ema50_series = ta.ema(m1_df, length=50)

        latest_rsi = rsi_series.iloc[-1]
        m5_ema50 = ema50_series.iloc[-1]
        m5_ema200 = ema200_series.iloc[-1]
        m1_ema50 = m1_ema50_series.iloc[-1]

        now = time.time()

        # --- CRASH LOGIC ---
        if "Crash" in symbol and m5_ema50 < m5_ema200:
            # Pre-Alert (RSI 60-70)
            if 60 <= latest_rsi < 70 and abs(latest_price - m1_ema50) <= 80:
                if now - last_pre_alert[symbol] > 600:
                    send_telegram(f"⚠️ *PRE-SIGNAL: {symbol}*\nRSI is {latest_rsi:.2f}. Price is approaching the EMA 50. Prepare to SELL.")
                    last_pre_alert[symbol] = now
            
            # Final Signal
            if latest_rsi >= 70 and abs(latest_price - m1_ema50) <= 50:
                send_telegram(f"🔻 *{symbol} SELL SIGNAL*\nEntry: {latest_price}\nRSI: {latest_rsi:.2f}")

        # --- BOOM LOGIC ---
        elif "Boom" in symbol and m5_ema50 > m5_ema200:
            # Pre-Alert (RSI 30-40)
            if 30 < latest_rsi <= 40 and abs(latest_price - m1_ema50) <= 80:
                if now - last_pre_alert[symbol] > 600:
                    send_telegram(f"⚠️ *PRE-SIGNAL: {symbol}*\nRSI is {latest_rsi:.2f}. Price is approaching the EMA 50. Prepare to BUY.")
                    last_pre_alert[symbol] = now

            # Final Signal
            if latest_rsi <= 30 and abs(latest_price - m1_ema50) <= 50:
                send_telegram(f"🚀 *{symbol} BUY SIGNAL*\nEntry: {latest_price}\nRSI: {latest_rsi:.2f}")

    except Exception as e:
        print(f"Analysis Error: {e}")
