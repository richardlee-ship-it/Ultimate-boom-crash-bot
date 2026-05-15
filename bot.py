import os
import json
import time
import requests
import pandas as pd

# =====================================
# BOT CONFIG
# =====================================
BOT_NAME = "🚀 Ultimate Boom & Crash Bot Spike Engine"

# Railway picks these up from your variables tab
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
DERIV_APP_ID = "1089"

last_signal_time = {}
COOLDOWN = 300  # 5 minutes spacing between alerts on the same pair

# Dict mapping pairs to their proper display names
SYMBOLS = {
    "BOOM1000": "Boom 1000 Index",
    "CRASH1000": "Crash 1000 Index",
    "BOOM500": "Boom 500 Index",
    "CRASH500": "Crash 500 Index",
    "CRASH900": "Crash 900 Index"
}

# =====================================
# TELEGRAM SYSTEM (HARD-CODED LINK SAFEGUARD)
# =====================================
def send_telegram(message):
    if not BOT_TOKEN or not CHAT_ID:
        print("⚠️ Missing Token or Chat ID setup inside environment tabs.")
        return
        
    # Clean any accidental spaces or hidden break characters from your Railway variable
    clean_token = str(BOT_TOKEN).strip()
    clean_chat_id = str(CHAT_ID).strip()
    
    # Absolute core URL structure to prevent any parsing errors
    url = f"https://telegram.org{clean_token}/sendMessage"
    
    try:
        response = requests.post(
            url, 
            data={"chat_id": clean_chat_id, "text": message}, 
            timeout=10
        )
        if response.status_code != 200:
            print(f"❌ Telegram API Error: {response.text}")
    except Exception as e:
        print(f"❌ Web Alert Network Fault: {e}")

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
    avg_loss = avg_loss.replace(0, 0.00001)  # Safeguard division errors
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# =====================================
# EMA CLOSE POSITION EVALUATION
# =====================================
def near_ema(price, ema_value, threshold=2.5):
    # Triggers if the current price is within 2.5 points of the indicator line
    return abs(price - ema_value) <= threshold

# =====================================
# RISK STRATEGY PARAMETERS (Strict 1:3 RR Ratio)
# =====================================
def get_sl_tp(entry, direction):
    risk = 20    # Your 20 Points Stop Loss Cushion
    reward = 60  # Your strict 1:3 Profit Target (20 * 3 = 60)

    if direction == "BUY":
        sl = entry - risk
        tp = entry + reward
    else:
        sl = entry + risk
        tp = entry - reward
    return sl, tp

# =====================================
# CLOUD BACKEND REST API CANDLE ENGINE
# =====================================
def fetch_deriv_candles(symbol, timeframe_minutes):
    """Bypasses custom web sockets by using standard unblocked web pools."""
    granularity = timeframe_minutes * 60
    url = f"https://derivws.com{symbol}&granularity={granularity}&count=100"
    
    try:
        response = requests.get(url, timeout=12)
        if response.status_code == 200:
            candles_data = response.json().get("candles", [])
            if candles_data:
                df = pd.DataFrame(candles_data)
                df["close"] = pd.to_numeric(df["close"])
                return df
    except Exception as network_error:
        print(f"⚠️ Engine data pooling lag on {symbol}: {network_error}")
    return None

# =====================================
# SIGNAL ANALYSIS ENGINE
# =====================================
def process_market_analysis(symbol):
    m1_df = fetch_deriv_candles(symbol, 1)   # 1-Minute Engine
    m5_df = fetch_deriv_candles(symbol, 5)   # 5-Minute Engine

    if m1_df is None or m5_df is None or len(m1_df) < 30 or len(m5_df) < 30:
        return

    # 1. M5 TREND FILTERS (50 EMA & 200 EMA)
    m5_close = m5_df["close"]
    m5_ema50 = ema(m5_close, 50).iloc[-1]
    m5_ema200 = ema(m5_close, 200).iloc[-1]

    bullish_trend = (m5_ema50 > m5_ema200)
    bearish_trend = (m5_ema50 < m5_ema200)

    # 2. M1 ENTRY PATTERN RULES
    m1_close = m1_df["close"]
    latest_price = m1_close.iloc[-1]
    m1_ema50 = ema(m1_close, 50).iloc[-1]
    m1_ema200 = ema(m1_close, 200).iloc[-1]
    
    # 3. MOMENTUM FILTER: 7-Period RSI at your required levels (80/20 setup)
    latest_rsi = rsi(m1_close, 7).iloc[-1]

    pair_name = SYMBOLS[symbol]
    now = time.time()
    last = last_signal_time.get(symbol, 0)

    if now - last < COOLDOWN:
        return

    # FEATURE A: BOOM BUY ENGINE RULES (M5 Bullish Trend + RSI Under 20 + Pullback to M1 EMA)
    if bullish_trend and latest_rsi <= 20 and (near_ema(latest_price, m1_ema50) or near_ema(latest_price, m1_ema200)):
        sl, tp = get_sl_tp(latest_price, "BUY")
        send_telegram(
            f"{BOT_NAME}\n\n🚀 BOOM SPIKE BUY SIGNAL\n\nPAIR: {pair_name}\n\n"
            f"📈 M5 Trend Filter: Bullish Trend (EMA 50 > 200) ✅\n"
            f"📊 RSI(7): {latest_rsi:.2f} (Oversold <= 20) ✅\n"
            f"🎯 EMA Zone Strategy: Pullback Active ✅\n\n"
            f"ENTRY: {latest_price:.2f}\n"
            f"SL (20 pts cushion): {sl:.2f}\n"
            f"TP (1:3 Target / 60 pts): {tp:.2f}"
        )
        last_signal_time[symbol] = now

    # FEATURE B: CRASH SELL ENGINE RULES (M5 Bearish Trend + RSI Over 80 + Pullback to M1 EMA)
    elif bearish_trend and latest_rsi >= 80 and (near_ema(latest_price, m1_ema50) or near_ema(latest_price, m1_ema200)):
        sl, tp = get_sl_tp(latest_price, "SELL")
        send_telegram(
            f"{BOT_NAME}\n\n🔻 CRASH SPIKE SELL SIGNAL\n\nPAIR: {pair_name}\n\n"
            f"📉 M5 Trend Filter: Bearish Trend (EMA 50 < 200) ✅\n"
            f"📊 RSI(7): {latest_rsi:.2f} (Overbought >= 80) ✅\n"
            f"🎯 EMA Zone Strategy: Pullback Active ✅\n\n"
            f"ENTRY: {latest_price:.2f}\n"
            f"SL (20 pts cushion): {sl:.2f}\n"
            f"TP (1:3 Target / 60 pts): {tp:.2f}"
        )
        last_signal_time[symbol] = now

# =====================================
# RAILWAY RUNNING ENVIRONMENT LIFELINE
# =====================================
def start_dummy_server():
    """Keeps Railway web engines alive by hosting a micro port endpoint."""
    import http.server
    import socketserver
    import threading

    class DummyHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Spike Scanning Engine Active")

    port = int(os.getenv("PORT", 8080))
    
    def server_thread():
        socketserver.TCPServer.allow_reuse_address = True
        with socketserver.TCPServer(("0.0.0.0", port), DummyHandler) as httpd:
            print(f"🌍 Railway web lifeline open on port {port}")
            httpd.serve_forever()
            
    threading.Thread(target=server_thread, daemon=True).start()

# =====================================
# MAIN RUN ENGINE
# =====================================
if __name__ == "__main__":
    print("🚀 Initializing Rest Loop Framework...")
    start_dummy_server()
    
    # Broadcast boot setup verification alert to your Telegram channel right away
    send_telegram(f"{BOT_NAME}\n\n✅ Cloud REST Engine Live on Railway 24/7\n\nStrategy Active:\n• M5 Trend Filters (50/200 EMA)\n• M1 Touch Pullbacks\n• RSI (80/20)\n• 1:3 Risk Target")
    
    while True:
        print("📊 Scanning Boom & Crash market variants across parameters...")
        for ticker in SYMBOLS.keys():
            process_market_analysis(ticker)
            time.sleep(2)  # Generates processing space between asset checks
            
        # Puts scanner to rest for 15 seconds before pulling next sequence of checks
        time.sleep(15)
