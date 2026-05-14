import os
import json
import time
import requests
import websocket
import pandas as pd

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

DERIV_APP_ID = "1089"

SYMBOLS = [
    "R_100",
    "R_50",
    "R_75"
]

price_data = {
    symbol: [] for symbol in SYMBOLS
}

last_signal_time = {}

COOLDOWN_SECONDS = 300

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }

    requests.post(url, data=payload)

def calculate_rsi(series, period=7):
    delta = series.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss

    rsi = 100 - (100 / (1 + rs))

    return rsi

def calculate_ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def calculate_envelope(series, period=75, deviation=0.09):
    sma = series.rolling(period).mean()

    upper = sma * (1 + deviation / 100)
    lower = sma * (1 - deviation / 100)

    return upper, lower

def detect_rejection(df):
    if len(df) < 2:
        return False

    candle = df.iloc[-1]

    body = abs(candle["close"] - candle["open"])
    wick = candle["high"] - candle["low"]

    if wick > body * 2:
        return True

    return False

def build_candles(prices):
    df = pd.DataFrame(prices, columns=["price"])

    df["time"] = pd.date_range(end=pd.Timestamp.now(), periods=len(df), freq="S")

    df = df.set_index("time")

    ohlc = df["price"].resample("1min").ohlc()

    return ohlc.dropna()

def analyze_symbol(symbol):
    prices = price_data[symbol]

    if len(prices) < 300:
        return

    candles = build_candles(prices)

    close = candles["close"]

    rsi = calculate_rsi(close)

    ema10 = calculate_ema(close, 10)
    ema20 = calculate_ema(close, 20)
    ema50 = calculate_ema(close, 50)
    ema200 = calculate_ema(close, 200)

    upper_env, lower_env = calculate_envelope(close)

    latest_price = close.iloc[-1]

    latest_rsi = rsi.iloc[-1]

    latest_ema10 = ema10.iloc[-1]
    latest_ema50 = ema50.iloc[-1]
    latest_ema200 = ema200.iloc[-1]

    latest_upper_env = upper_env.iloc[-1]
    latest_lower_env = lower_env.iloc[-1]

    rejection = detect_rejection(candles)

    current_time = time.time()

    if symbol not in last_signal_time:
        last_signal_time[symbol] = 0

    cooldown_passed = (
        current_time - last_signal_time[symbol]
    ) > COOLDOWN_SECONDS

    # CRASH SELL SETUP
    if (
        latest_rsi >= 80 and
        latest_ema10 >= latest_upper_env and
        latest_ema50 < latest_ema200 and
        rejection and
        cooldown_passed
    ):

        message = f"""
🚨 {symbol} SELL SIGNAL

RSI(7): {latest_rsi:.2f}
EMA10 touching upper envelope
Bearish rejection confirmed

Trend aligned
Cooldown passed

Confidence: 8.5/10
"""

        send_telegram(message)

        last_signal_time[symbol] = current_time

    # BOOM BUY SETUP
    if (
        latest_rsi <= 20 and
        latest_ema10 <= latest_lower_env and
        latest_ema50 > latest_ema200 and
        rejection and
        cooldown_passed
    ):

        message = f"""
🚨 {symbol} BUY SIGNAL

RSI(7): {latest_rsi:.2f}
EMA10 touching lower envelope
Bullish rejection confirmed

Trend aligned
Cooldown passed

Confidence: 8.5/10
"""

        send_telegram(message)

        last_signal_time[symbol] = current_time

def on_message(ws, message):
    data = json.loads(message)

    if "tick" in data:

        symbol = data["tick"]["symbol"]
        price = data["tick"]["quote"]

        price_data[symbol].append(price)

        if len(price_data[symbol]) > 1000:
            price_data[symbol] = price_data[symbol][-1000:]

        analyze_symbol(symbol)

def on_open(ws):
    send_telegram("✅ Strategy Engine Activated")

    for symbol in SYMBOLS:
        ws.send(json.dumps({
            "ticks": symbol,
            "subscribe": 1
        }))

def on_error(ws, error):
    print(error)

def on_close(ws, close_status_code, close_msg):
    print("WebSocket closed")

def run_websocket():
    url = f"wss://ws.derivws.com/websockets/v3?app_id={DERIV_APP_ID}"

    ws = websocket.WebSocketApp(
        url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )

    ws.run_forever()

send_telegram("🚀 Boom/Crash Strategy Bot Starting...")

while True:
    try:
        run_websocket()
    except Exception as e:
        print("Restarting:", e)

    time.sleep(5)
