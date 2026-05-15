import os
import json
import time
import requests
import websocket
import pandas as pd
from datetime import datetime

# =====================================
# BOT CONFIG
# =====================================
BOT_NAME = "🚀 Ultimate Boom & Crash Bot Spike Engine"
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
DERIV_APP_ID = "1089"

# =====================================
# SYMBOLS
# =====================================
SYMBOLS = {
    "BOOM1000": "Boom 1000 Index",
    "CRASH1000": "Crash 1000 Index",
    "BOOM500": "Boom 500 Index",
    "CRASH500": "Crash 500 Index",
    "CRASH900": "Crash 900 Index"
}

# =====================================
# STORAGE & SETTINGS
# =====================================
tick_data = {s: [] for s in SYMBOLS}
last_signal_time = {}
active_trade = {}
COOLDOWN = 300 

# =====================================
# TELEGRAM
# =====================================
def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": message})
    except Exception as e:
        print("Telegram Error:", e)

# =====================================
# INDICATORS
# =====================================
def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def rsi(series, period=7):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    avg_loss = avg_loss.replace(0, 0.00001)
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# =====================================
# BUILD CANDLES
# =====================================
def build_candles(prices, tf="1min"):
    df = pd.DataFrame(prices, columns=["price"])
    # We use a frequency of 1s as a fallback for tick data spacing
    df["time"] = pd.date_range(end=pd.Timestamp.now(), periods=len(df), freq="s")
    df = df.set_index("time")
    ohlc = df["price"].resample(tf).ohlc()
    return ohlc.dropna()

def near_ema(price, ema_value, threshold=20):
    return abs(price - ema_value) <= threshold

def get_sl_tp(entry, direction):
    risk, reward = 20, 60
    if direction == "BUY":
        return entry - risk, entry + reward
    return entry + risk, entry - reward

# =====================================
# ANALYSIS ENGINE
# =====================================
def analyze(symbol):
    prices = tick_data[symbol]
    
    # We now check for 1000 ticks to ensure enough M5 candles
    if len(prices) < 1000:
        return

    m1 = build_candles(prices, "1min")
    m5 = build_candles(prices, "5min")

    if len(m1) < 20 or len(m5) < 20:
        return

    # TREND LOGIC (M5)
    m5_close = m5["close"]
    m5_ema50 = ema(m5_close, 50).iloc[-1]
    m5_ema200 = ema(m5_close, 200).iloc[-1]

    # ENTRY LOGIC (M1)
    m1_close = m1["close"]
    latest_price = m1_close.iloc[-1]
    m1_ema50_val = ema(m1_close, 50).iloc[-1]
    m1_ema200_val = ema(m1_close, 200).iloc[-1]
    latest_rsi = rsi(m1_close, 7).iloc[-1]

    now = time.time()
    if (now - last_signal_time.get(symbol, 0) < COOLDOWN) or (symbol in active_trade):
        return

    # BUY CONDITION (Boom)
    if (m5_ema50 > m5_ema200) and (latest_rsi <= 30) and \
       (near_ema(latest_price, m1_ema50_val) or near_ema(latest_price, m1_ema200_val)):
        
        sl, tp = get_sl_tp(latest_price, "BUY")
        send_telegram(f"🚀 {SYMBOLS[symbol]} BUY\nEntry: {latest_price:.2f}\nSL: {sl:.2f}\nTP: {tp:.2f}")
        active_trade[symbol] = {"direction": "BUY", "tp": tp, "sl": sl, "pair": SYMBOLS[symbol]}
        last_signal_time[symbol] = now

    # SELL CONDITION (Crash)
    elif (m5_ema50 < m5_ema200) and (latest_rsi >= 70) and \
         (near_ema(latest_price, m1_ema50_val) or near_ema(latest_price, m1_ema200_val)):
        
        sl, tp = get_sl_tp(latest_price, "SELL")
        send_telegram(f"🔻 {SYMBOLS[symbol]} SELL\nEntry: {latest_price:.2f}\nSL: {sl:.2f}\nTP: {tp:.2f}")
        active_trade[symbol] = {"direction": "SELL", "tp": tp, "sl": sl, "pair": SYMBOLS[symbol]}
        last_signal_time[symbol] = now

# =====================================
# WEBSOCKET HANDLERS
# =====================================
def on_message(ws, message):
    data = json.loads(message)
    
    # Process History Data
    if "history" in data:
        symbol = data["echo_req"]["ticks_history"]
        prices = [float(p) for p in data["history"]["prices"]]
        tick_data[symbol] = prices
        print(f"✅ Pre-loaded {len(prices)} ticks for {symbol}")

    # Process Live Ticks
    if "tick" in data:
        symbol = data["tick"]["symbol"]
        price = data["tick"]["quote"]
        if symbol in tick_data:
            tick_data[symbol].append(price)
            if len(tick_data[symbol]) > 5000:
                tick_data[symbol] = tick_data[symbol][-5000:]
            
            # Check existing trades for TP/SL
            if symbol in active_trade:
                t = active_trade[symbol]
                if (t["direction"] == "BUY" and (price >= t["tp"] or price <= t["sl"])) or \
                   (t["direction"] == "SELL" and (price <= t["tp"] or price >= t["sl"])):
                    res = "PROFIT ✅" if (t["direction"]=="BUY" and price >= t["tp"]) or (t["direction"]=="SELL" and price <= t["tp"]) else "LOSS ❌"
                    send_telegram(f"Trade Closed: {t['pair']} - {res}")
                    del active_trade[symbol]

            analyze(symbol)

def on_open(ws):
    send_telegram(f"✅ {BOT_NAME} Connected. Fetching history...")
    for symbol in SYMBOLS.keys():
        ws.send(json.dumps({
            "ticks_history": symbol,
            "count": 3000,
            "end": "latest",
            "style": "ticks",
            "subscribe": 1
        }))

def run():
    ws = websocket.WebSocketApp(
        f"wss://ws.derivws.com/websockets/v3?app_id={DERIV_APP_ID}",
        on_open=on_open,
        on_message=on_message
    )
    ws.run_forever()

if __name__ == "__main__":
    while True:
        try:
            run()
        except:
            time.sleep(5)
