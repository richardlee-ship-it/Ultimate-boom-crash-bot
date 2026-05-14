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
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": msg
    })

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

# =========================
# REJECTION CANDLE
# =========================

def rejection(df):
    if len(df) < 2:
        return False

    c = df.iloc[-1]

    body = abs(c["close"] - c["open"])
    wick = c["high"] - c["low"]

    return wick > body * 2

# =========================
# BUILD M1 CANDLES
# =========================

def build_candles(prices):
    df = pd.DataFrame(prices, columns=["price"])

    df["time"] = pd.date_range(
        end=pd.Timestamp.now(),
        periods=len(df),
        freq="s"
    )

    df = df.set_index("time")

    ohlc = df["price"].resample("1min").ohlc()

    return ohlc.dropna()

# =========================
# SL TP ENGINE
# =========================

def get_sl_tp(entry, direction):

    if direction == "BUY":
        sl = entry - 15
        tp = entry + 30

    else:
        sl = entry + 15
        tp = entry - 30

    return sl, tp

# =========================
# EMA ZONE CHECK
# =========================

def near_ema(price, ema_value, distance=5):
    return abs(price - ema_value) <= distance

# =========================
# ANALYSIS
# =========================

def analyze(symbol):

    prices = price_data[symbol]

    if len(prices) < 300:
        return

    candles = build_candles(prices)

    close = candles["close"]

    e50 = ema(close, 50)
    e200 = ema(close, 200)

    r = rsi(close, 7)

    latest_price = close.iloc[-1]

    ema50 = e50.iloc[-1]
    ema200 = e200.iloc[-1]

    latest_rsi = r.iloc[-1]

    rej = rejection(candles)

    now = time.time()

    last = last_signal_time.get(symbol, 0)

    if now - last < COOLDOWN:
        return

    # =========================
    # BULLISH TREND
    # =========================

    bullish = ema50 > ema200

    # =========================
    # BEARISH TREND
    # =========================

    bearish = ema50 < ema200

    # =========================
    # BUY SIGNAL
    # =========================

    if (
        bullish and
        latest_rsi <= 20 and
        (
            near_ema(latest_price, ema50)
            or near_ema(latest_price, ema200)
        ) and
        rej
    ):

        sl, tp = get_sl_tp(latest_price, "BUY")

        msg = f"""
🚀 {symbol} BUY SIGNAL

Trend: Bullish
RSI(7): {latest_rsi:.2f}

Price touched EMA zone
Bullish rejection confirmed

Entry: {latest_price:.2f}
SL: {sl:.2f}
TP: {tp:.2f}
"""

        send_telegram(msg)

        last_signal_time[symbol] = now

    # =========================
    # SELL SIGNAL
    # =========================

    if (
        bearish and
        latest_rsi >= 80 and
        (
            near_ema(latest_price, ema50)
            or near_ema(latest_price, ema200)
        ) and
        rej
    ):

        sl, tp = get_sl_tp(latest_price, "SELL")

        msg = f"""
🔻 {symbol} SELL SIGNAL

Trend: Bearish
RSI(7): {latest_rsi:.2f}

Price touched EMA zone
Bearish rejection confirmed

Entry: {latest_price:.2f}
SL: {sl:.2f}
TP: {tp:.2f}
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

    send_telegram(
        "🚀 EMA Zone Spike Bot Online"
    )

    for s in SYMBOLS:

        ws.send(json.dumps({
            "ticks": s,
            "subscribe": 1
        }))

def run():

    url = (
        f"wss://ws.derivws.com/"
        f"websockets/v3?app_id={DERIV_APP_ID}"
    )

    ws = websocket.WebSocketApp(
        url,
        on_open=on_open,
        on_message=on_message
    )

    ws.run_forever()

send_telegram(
    "🚀 Boom/Crash EMA Zone Bot Starting..."
)

while True:

    try:
        run()

    except Exception as e:

        print("Restart:", e)

        time.sleep(5)
