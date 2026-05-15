import time, requests

# PASTE YOUR NEW TOKEN HERE
TOKEN = "8830024269: AAHe15l_My8tw3D2Vf7gH0yz7VEkgqbYwK8"
ID = "6856488919"

MARKETS = ["Crash 1000", "Boom 1000", "Crash 900", "Crash 500", "Boom 500"]

def send_msg(text):
    try:
        # This is the exact format Telegram needs
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": ID, "text": text}
        r = requests.post(url, json=payload)
        print(f"Telegram Status: {r.status_code}")
        if r.status_code != 200:
            print(f"Error detail: {r.text}")
    except:
        print("Connection Error")

if __name__ == "__main__":
    print("--- 🚀 BOT DEPLOYED 🚀 ---")
    send_msg("💎 SUCCESS! The connection is now perfect.")

    while True:
        for m in MARKETS:
            print(f"Scanning {m}...")
        time.sleep(60)
