import time
import requests

# MANUALLY TYPE THE TOKEN AND ID HERE
TOKEN = "8667543667:AAFFdhIPIjJGAVcbQ3be8wYgQQNvy_5mB9s"
CHAT_ID = "6856488919"

SYMBOLS = ["Crash 1000 Index", "Boom 1000 Index", "Crash 900 Index", "Crash 500 Index", "Boom 500 Index"]

def send_msg(text):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        params = {"chat_id": CHAT_ID, "text": text}
        r = requests.get(url, params=params)
        print(f"Status: {r.status_code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("--- SCANNER STARTING ---")
    send_msg("✅ MANUAL TYPE SUCCESS!")
    
    while True:
        for s in SYMBOLS:
            print(f"Scanning {s}")
        time.sleep(60)
