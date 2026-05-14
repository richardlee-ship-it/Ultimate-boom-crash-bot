import os
import json
import websocket
import requests
import threading
import time

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

DERIV_APP_ID = "1089"

SYMBOLS = [
    "R_100",
    "R_50",
    "R_75"
]

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }

    requests.post(url, data=payload)

def on_message(ws, message):
    data = json.loads(message)

    if "tick" in data:
        symbol = data["tick"]["symbol"]
        price = data["tick"]["quote"]

        print(f"{symbol}: {price}")

def on_open(ws):
    print("Connected to Deriv WebSocket")

    send_telegram("✅ Connected to Deriv Live Feed")

    for symbol in SYMBOLS:
        ws.send(json.dumps({
            "ticks": symbol,
            "subscribe": 1
        }))

def on_error(ws, error):
    print("Error:", error)

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

send_telegram("🚀 Boom/Crash Bot Starting...")

while True:
    try:
        run_websocket()
    except Exception as e:
        print("Restarting:", e)

    time.sleep(5)
