import os
import json
import time
import requests
import websocket
import pandas as pd

# =====================================
# CONFIG
# =====================================

BOT_NAME = "🚀 Ultimate Boom & Crash Bot Spike Engine"

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

DERIV_APP_ID = "1089"

SYMBOLS = {
    "BOOM1000": "Boom 1000 Index",
    "CRASH1000": "Crash 1000 Index",
    "BOOM500": "Boom 500 Index",
    "CRASH500": "Crash 500 Index",
    "CRASH900": "Crash 900 Index"
}

tick_data = {s: [] for s in SYMBOLS}

last_signal_time = {}

active_trade = {}

COOLDOWN = 180

# =====================================
# TELEGRAM
# =====================================

def send_telegram(message):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    try:

        response = requests.post(
            url,
            data={
                "chat_id": CHAT_ID,
                "text": message
            },
            timeout=10
        )

        print(response.text)

    except Exception as e:

        print("Telegram Error:", e)

# =====================================
# EMA
# =====================================

def ema(series, period):

    return series.ewm(
        span=period,
        adjust=False
    ).mean()

# =====================================
# RSI
# =====================================

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

def build_candles(prices, timeframe):

    df = pd.DataFrame(prices, columns=["price"])

    df["time"] = pd.date_range(
        end=pd.Timestamp.now(),
        periods=len(df),
        freq="s"
    )

    df = df.set_index("time")

    candles = df["price"].resample(timeframe).ohlc()

    return candles.dropna()

# =====================================
# EMA TOUCH
# =====================================

def near_ema(price, ema_value):

    return abs(price - ema_value) <= 50

# =====================================
# TP / SL
# =====================================

def get_sl_tp(entry, direction):

    risk = 20
    reward = 60

    if direction == "BUY":

        sl = entry - risk
        tp = entry + reward

    else:

        sl = entry + risk
        tp = entry - reward

    return sl, tp

# =====================================
# TRADE TRACKER
# =====================================

def check_trade_result(symbol, price):

    if symbol not in active_trade:
        return

    trade = active_trade[symbol]

    direction = trade["direction"]

    tp = trade["tp"]

    sl = trade["sl"]

    pair = trade["pair"]

    if direction == "BUY":

        if price >= tp:

            send_telegram(
f"🎯 TP HIT\n\n{pair}\n\nBUY closed in profit ✅"
            )

            del active_trade[symbol]

        elif price <= sl:

            send_telegram(
f"❌ SL HIT\n\n{pair}\n\nBUY stopped out"
            )

            del active_trade[symbol]

    else:

        if price <= tp:

            send_telegram(
f"🎯 TP HIT\n\n{pair}\n\nSELL closed in profit ✅"
            )

            del active_trade[symbol]

        elif price >= sl:

            send_telegram(
f"❌ SL HIT\n\n{pair}\n\nSELL stopped out"
            )

            del active_trade[symbol]

# =====================================
# ANALYSIS
# =====================================

def analyze(symbol):

    prices = tick_data[symbol]

    if len(prices) < 1200:
        return

    # =================================
    # MULTI TIMEFRAME
    # =================================

    m1 = build_candles(prices, "1min")

    m5 = build_candles(prices, "5min")

    if len(m1) < 220 or len(m5) < 220:
        return

    # =================================
    # M5 TREND
    # =================================

    m5_close = m5["close"]

    m5_ema50 = ema(m5_close, 50)

    m5_ema200 = ema(m5_close, 200)

    bullish_trend = (
        m5_ema50.iloc[-1] >
        m5_ema200.iloc[-1]
    )

    bearish_trend = (
        m5_ema50.iloc[-1] <
        m5_ema200.iloc[-1]
    )

    # =================================
    # M1 ENTRY
    # =================================

    m1_close = m1["close"]

    latest_price = m1_close.iloc[-1]

    m1_ema50 = ema(m1_close, 50)

    m1_ema200 = ema(m1_close, 200)

    latest_rsi = rsi(m1_close, 7).iloc[-1]

    pair_name = SYMBOLS[symbol]

    now = time.time()

    last = last_signal_time.get(symbol, 0)

    if now - last < COOLDOWN:
        return

    if symbol in active_trade:
        return

    # =================================
    # BUY SIGNAL
    # =================================

    if (

        bullish_trend and

        latest_rsi <= 30 and

        (
            near_ema(
                latest_price,
                m1_ema50.iloc[-1]
            )

            or

            near_ema(
                latest_price,
                m1_ema200.iloc[-1]
            )
        )

    ):

        sl, tp = get_sl_tp(
            latest_price,
            "BUY"
        )

        send_telegram(
f"""
{BOT_NAME}

🚀 BOOM BUY SIGNAL

PAIR: {pair_name}

📈 M5 TREND: BULLISH
📊 RSI(7): {latest_rsi:.2f}
🎯 EMA PULLBACK CONFIRMED

ENTRY: {latest_price:.2f}
SL: {sl:.2f}
TP: {tp:.2f}
"""
        )

        active_trade[symbol] = {
            "direction": "BUY",
            "entry": latest_price,
            "sl": sl,
            "tp": tp,
            "pair": pair_name
        }

        last_signal_time[symbol] = now

    # =================================
    # SELL SIGNAL
    # =================================

    elif (

        bearish_trend and

        latest_rsi >= 70 and

        (
            near_ema(
                latest_price,
                m1_ema50.iloc[-1]
            )

            or

            near_ema(
                latest_price,
                m1_ema200.iloc[-1]
            )
        )

    ):

        sl, tp = get_sl_tp(
            latest_price,
            "SELL"
        )

        send_telegram(
f"""
{BOT_NAME}

🔻 CRASH SELL SIGNAL

PAIR: {pair_name}

📉 M5 TREND: BEARISH
📊 RSI(7): {latest_rsi:.2f}
🎯 EMA PULLBACK CONFIRMED

ENTRY: {latest_price:.2f}
SL: {sl:.2f}
TP: {tp:.2f}
"""
        )

        active_trade[symbol] = {
            "direction": "SELL",
            "entry": latest_price,
            "sl": sl,
            "tp": tp,
            "pair": pair_name
        }

        last_signal_time[symbol] = now

# =====================================
# WEBSOCKET
# =====================================

def on_message(ws, message):

    data = json.loads(message)

    if "tick" in data:

        symbol = data["tick"]["symbol"]

        price = data["tick"]["quote"]

        if symbol not in tick_data:
            return

        tick_data[symbol].append(price)

        if len(tick_data[symbol]) > 6000:

            tick_data[symbol] = (
                tick_data[symbol][-6000:]
            )

        check_trade_result(symbol, price)

        analyze(symbol)

# =====================================
# OPEN
# =====================================

def on_open(ws):

    send_telegram(
f"""
{BOT_NAME}

✅ Multi-Timeframe Spike Engine Active
"""
    )

    for symbol in SYMBOLS.keys():

        ws.send(json.dumps({
            "ticks": symbol,
            "subscribe": 1
        }))

# =====================================
# RUN
# =====================================

def run():

    url = (
        f"wss://ws.derivws.com/websockets/v3?app_id={DERIV_APP_ID}"
    )

    ws = websocket.WebSocketApp(
        url,
        on_open=on_open,
        on_message=on_message
    )

    ws.run_forever()

# =====================================
# START
# =====================================

send_telegram(
f"{BOT_NAME}\n\n🚀 Starting..."
)

while True:

    try:

        run()

    except Exception as e:

        print("Restarting:", e)

        time.sleep(5)
