import os
import json
import time
import requests
import websocket
import pandas as pd

# =========================
# CONFIG
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

DERIV_APP_ID = "1089"

SYMBOLS = ["R_100", "R_50", "R_75"]

price_data = {s: [] for s in SYMBOLS}
last_signal_time = {}

COOLDOWN = 300

# =========================
# TELEGRAM
# =========================

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# =========================
# INDICATORS
# =========================

def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def rsi(series, period=7):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def envelope(series, period=75, dev=0.09):
    sma = series.rolling(period).mean()
    upper = sma * (1 + dev / 100)
    lower = sma * (1 - dev / 100)
    return upper, lower

def rejection(df):
    if len(df) < 2:
        return False

    c = df.iloc[-1]
    body = abs(c["close"] - c["open"])
    wick = c["high"] - c["low"]

    return wick > body * 2

# =========================
# SPIKE EXHAUSTION FILTER
# =========================

def spike_exhaustion(rsi_series, direction):
    if len(rsi_series) < 3:
        return False

    curr = rsi_series.iloc[-1]
    prev = rsi_series.iloc[-2]

    if direction == "BUY":
        return curr <= 15 and curr > prev

    if direction == "SELL":
        return curr >= 85 and curr < prev

    return False

# =========================
# CANDLE BUILDER
# =========================

def build_candles(prices):
    df = pd.DataFrame(prices, columns=["price"])
    df["time"] = pd.date_range(end=pd.Timestamp.now(), periods=len(df), freq="S")
    df = df.set_index("time")

    ohlc = df["price"].resample("1min").ohlc()
    return ohlc.dropna()

# =========================
# SL / TP ENGINE
# =========================

def sl_tp(entry, upper, lower, direction):
    width = abs(upper - lower)
    buffer = width * 0.1

    if direction == "SELL":
        sl = upper + buffer
        tp = entry - (sl - entry) * 1.5
    else:
        sl = lower - buffer
        tp = entry + (entry - sl) * 1.5

    return sl, tp

# =========================
# ANALYSIS ENGINE
# =========================

def analyze(symbol):
    prices = price_data[symbol]

    if len(prices) < 300:
        return

    candles = build_candles(prices)
    close = candles["close"]

    r = rsi(close, 7)
    e10 = ema(close, 10)
    e50 = ema(close, 50)
    e200 = ema(close, 200)
    upper, lower = envelope(close)

    if len(close) < 200:
        return

    entry = close.iloc[-1]

    latest_rsi = r.iloc[-1]
    ema10 = e10.iloc[-1]
    ema50 = e50.iloc[-1]
    ema200 = e200.iloc[-1]

    up = upper.iloc[-1]
    low = lower.iloc[-1]

    rej = rejection(candles)

    now = time.time()
    last = last_signal_time.get(symbol, 0)

    if now - last < COOLDOWN:
        return

    # =========================
    # SELL (CRASH EXHAUSTION)
    # =========================

    if (
        latest_rsi >= 85 and
        ema10 >= up and
        ema50 < ema200 and
        rej and
        spike_exhaustion(r, "SELL")
    ):

        sl, tp = sl_tp(entry, up, low, "SELL")

        msg = f"""
🚨 {symbol} SELL SIGNAL

RSI(7): {latest_rsi:.2f}
EMA10 upper envelope touch
Bearish rejection confirmed
Spike exhaustion confirmed

Entry: {entry:.2f}
SL: {sl:.2f}
TP: {tp:.2f}
RR: 1:1.5
"""

        send_telegram(msg)
        last_signal_time[symbol] = now

    # =========================
    # BUY (BOOM EXHAUSTION)
    # =========================

    if (
        latest_rsi <= 15 and
        ema10 <= low and
        ema50 > ema200 and
        rej and
        spike_exhaustion(r, "BUY")
    ):

        sl, tp = sl_tp(entry, up, low, "BUY")

        msg = f"""
🚀 {symbol} BUY SIGNAL

RSI(7): {latest_rsi:.2f}
EMA10 lower envelope touch
Bullish rejection confirmed
Spike exhaustion confirmed

Entry: {entry:.2f}
SL: {sl:.2f}
TP: {tp:.2f}
RR: 1:1.5
"""

        send_telegram(msg)
        last_signal_time[symbol] = now

# =========================
# WEBSOCKET
# =========================

def on_message(ws, message):
    data = json.loads(message)

    if "tick" in data:
        sym = data["tick"]["symbol"]
        price = data["tick"]["quote"]

        price_data[sym].append(price)

        if len(price_data[sym]) > 1000:
            price_data[sym] = price_data[sym][-1000:]

        analyze(sym)

def on_open(ws):
    send_telegram("🚀 Strategy Bot Online (Spike Engine Active)")

    for s in SYMBOLS:
        ws.send(json.dumps({"ticks": s, "subscribe": 1}))

def run():
    url = f"wss://ws.derivws.com/websockets/v3?app_id={DERIV_APP_ID}"

    ws = websocket.WebSocketApp(url, on_open=on_open, on_message=on_message)
    ws.run_forever()

send_telegram("🚀 Boom/Crash Bot Starting...")

while True:
    try:
        run()
    except Exception as e:
        print("Restart:", e)
        time.sleep(5)
