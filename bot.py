import os
import json
import time
import requests
import websocket
import pandas as pd

# =====================================
# BOT CONFIG
# =====================================
BOT_NAME = "🚀 Ultimate Boom & Crash Bot Spike Engine"

# Railway picks these up seamlessly if set in the variables tab
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
# STORAGE (Saves timestamps alongside tick data)
# =====================================
tick_data = {s: [] for s in SYMBOLS}
tick_times = {s: [] for s in SYMBOLS}
last_signal_time = {}
active_trade = {}
COOLDOWN = 300  # Reduced to 5 minutes to accommodate rapid M1 setups

# =====================================
# TELEGRAM SYSTEM
# =====================================
def send_telegram(message):
    if not BOT_TOKEN or not CHAT_ID:
        print("⚠️ Missing Token or Chat ID configuration variables.")
        return
    url = f"https://telegram.org{BOT_TOKEN}/sendMessage"
    try:
        response = requests.post(url, data={"chat_id": CHAT_ID, "text": message})
        if response.status_code != 200:
            print(f"❌ Telegram Error: {response.text}")
    except Exception as e:
        print(f"❌ Network Error to Telegram: {e}")

# =====================================
# TECHNICAL INDICATORS
# =====================================
def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def rsi(series, period=7):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    # Avoid zero division errors
    avg_loss = avg_loss.replace(0, 0.00001)
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# =====================================
# FIXED CANDLE RESAMPLER
# =====================================
def build_candles(symbol, tf="1min"):
    prices = tick_data[symbol]
    times = tick_times[symbol]
    
    df = pd.DataFrame({"price": prices, "time": pd.to_datetime(times, unit='s')})
    df = df.set_index("time")
    
    # Resample using actual time windows
    ohlc = df["price"].resample(tf).ohlc()
    return ohlc.ffill().dropna()

# =====================================
# EMA TOUCH (Adjusted margin for asset scaling)
# =====================================
def near_ema(price, ema_value, threshold=2.5):
    return abs(price - ema_value) <= threshold

# =====================================
# TAILORED RISK MANAGEMENT (1:3 Risk/Reward)
# =====================================
def get_sl_tp(entry, direction):
    risk = 20   # Equivalent to approximately 20 M1 candles
    reward = 60 # Strict 1:3 Risk to Reward execution

    if direction == "BUY":
        sl = entry - risk
        tp = entry + reward
    else:
        sl = entry + risk
        tp = entry - reward
    return sl, tp

# =====================================
# TRADE RESULTS TRACKER
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
            send_telegram(f"🎯 TP HIT ✅\n\n{pair}\n\nBUY closed in 1:3 profit target.")
            del active_trade[symbol]
        elif price <= sl:
            send_telegram(f"❌ SL HIT 🩸\n\n{pair}\n\nBUY stopped out (20 pt cushion).")
            del active_trade[symbol]
    else:
        if price <= tp:
            send_telegram(f"🎯 TP HIT ✅\n\n{pair}\n\nSELL closed in 1:3 profit target.")
            del active_trade[symbol]
        elif price >= sl:
            send_telegram(f"❌ SL HIT 🩸\n\n{pair}\n\nSELL stopped out (20 pt cushion).")
            del active_trade[symbol]

# =====================================
# OPTIMIZED ANALYSIS ENGINE
# =====================================
def analyze(symbol):
    if len(tick_data[symbol]) < 250:
        return

    m1 = build_candles(symbol, "1min")
    m5 = build_candles(symbol, "5min")

    if len(m1) < 15 or len(m5) < 15:
        return

    # M5 TREND FILTERS
    m5_close = m5["close"]
    m5_ema50 = ema(m5_close, 50)
    m5_ema200 = ema(m5_close, 200)

    bullish_trend = (m5_ema50.iloc[-1] > m5_ema200.iloc[-1])
    bearish_trend = (m5_ema50.iloc[-1] < m5_ema200.iloc[-1])

    # M1 EXECUTION SPECS
    close = m1["close"]
    latest_price = close.iloc[-1]
    m1_ema50 = ema(close, 50).iloc[-1]
    m1_ema200 = ema(close, 200).iloc[-1]
    
    # RSI parameters to your required 80/20 criteria
    latest_rsi = rsi(close, 7).iloc[-1]

    pair_name = SYMBOLS[symbol]
    now = time.time()
    last = last_signal_time.get(symbol, 0)

    if now - last < COOLDOWN or symbol in active_trade:
        return

    # CRITERIA A: BOOM/BUY ALERTS (RSI <= 20 + M5 Bullish + EMA Support Zone)
    if bullish_trend and latest_rsi <= 20 and (near_ema(latest_price, m1_ema50) or near_ema(latest_price, m1_ema200)):
        sl, tp = get_sl_tp(latest_price, "BUY")
        send_telegram(f"{BOT_NAME}\n\n🚀 BOOM SPIKE BUY SIGNAL\n\nPAIR: {pair_name}\n\nM5 Trend Filter: Bullish Trend (EMA 50 > 200) ✅\nRSI(7): {latest_rsi:.2f} (Oversold <= 20)\nEMA Zone Strategy: Pullback Active\n\nENTRY: {latest_price:.2f}\nSL (20 pts): {sl:.2f}\nTP (60 pts): {tp:.2f}")
        active_trade[symbol] = {"direction": "BUY", "entry": latest_price, "sl": sl, "tp": tp, "pair": pair_name}
        last_signal_time[symbol] = now

    # CRITERIA B: CRASH/SELL ALERTS (RSI >= 80 + M5 Bearish + EMA Resistance Zone)
    elif bearish_trend and latest_rsi >= 80 and (near_ema(latest_price, m1_ema50) or near_ema(latest_price, m1_ema200)):
        sl, tp = get_sl_tp(latest_price, "SELL")
        send_telegram(f"{BOT_NAME}\n\n🔻 CRASH SPIKE SELL SIGNAL\n\nPAIR: {pair_name}\n\nM5 Trend Filter: Bearish Trend (EMA 50 < 200) ✅\nRSI(7): {latest_rsi:.2f} (Overbought >= 80)\nEMA Zone Strategy: Pullback Active\n\nENTRY: {latest_price:.2f}\nSL (20 pts): {sl:.2f}\nTP (60 pts): {tp:.2f}")
        active_trade[symbol] = {"direction": "SELL", "entry": latest_price, "sl": sl, "tp": tp, "pair": pair_name}
        last_signal_time[symbol] = now

# =====================================
# WEBSOCKET MANAGER
# =====================================
def on_message(ws, message):
    data = json.loads(message)
    
    if "history" in data:
        symbol = data["echo_req"]["ticks_history"]
        if symbol in tick_data:
            tick_data[symbol] = data["history"]["prices"]
            tick_times[symbol] = data["history"]["times"]
            print(f"📊 Preloaded {len(tick_data[symbol])} core history points for {symbol}")
            return

    if "tick" in data:
        symbol = data["tick"]["symbol"]
        price = data["tick"]["quote"]
        timestamp = data["tick"]["epoch"]

        if symbol not in tick_data:
            return

        tick_data[symbol].append(price)
        tick_times[symbol].append(timestamp)

        if len(tick_data[symbol]) > 2000:
            tick_data[symbol] = tick_data[symbol][-2000:]
            tick_times[symbol] = tick_times[symbol][-2000:]

        check_trade_result(symbol, price)
        analyze(symbol)

def on_open(ws):
    print("📡 Connection to Deriv Server established successfully.")
    send_telegram(f"{BOT_NAME}\n\n✅ Live Setup Active on Railway Server")

    for symbol in SYMBOLS.keys():
        # Requests past history ticks to prevent startup delays
        ws.send(json.dumps({
            "ticks_history": symbol,
            "adjust_start_time": 1,
            "count": 1500,
            "end": "latest",
            "style": "ticks"
        }))
        ws.send(json.dumps({"ticks": symbol, "subscribe": 1}))

# =====================================
# RUN & LOOP (FIXED WITH PRODUCTION URL & DUMMY PORT)
# =====================================
def start_dummy_server():
    """Keeps Railway alive by listening to the assigned system port."""
    import http.server
    import socketserver
    import threading

    class DummyHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot Engine is Active")

    port = int(os.getenv("PORT", 8080))
    
    def server_thread():
        # Fixes port re-use lock issues on rapid server crashes
        socketserver.TCPServer.allow_reuse_address = True
        with socketserver.TCPServer(("", port), DummyHandler) as httpd:
            print(f"🌍 Dummy server ticking on port {port}")
            httpd.serve_forever()
            
    threading.Thread(target=server_thread, daemon=True).start()

def run():
    # FIX: Swapped out broken domain for the official unblocked Deriv production endpoint
    url = f"wss://://derivws.com{DERIV_APP_ID}"
    ws = websocket.WebSocketApp(url, on_open=on_open, on_message=on_message)
    ws.run_forever()

if __name__ == "__main__":
    print("🚀 Initializing Bot Main Loop...")
    
    # Fire up the dummy server so Railway doesn't shut the container down
    start_dummy_server()
    
    while True:
        try:
            run()
        except Exception as error:
            print(f"⚠️ Process connection break: {error}. Retrying in 5s...")
            time.sleep(5)
