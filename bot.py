import time, requests

# PASTE YOUR NEW TOKEN HERE
TOKEN = "8830024269: AAHe15l_My8tw3D2Vf7gH0yz7VEkgqbYwK8"
ID = "6856488919"

# Markets you are trading
MARKETS = ["Crash 1000", "Boom 1000", "Crash 900", "Crash 500", "Boom 500"]

def send_msg(text):
    try:
        # Simplified URL for iPhone compatibility
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={ID}&text={text}"
        r = requests.get(url)
        print(f"Telegram Status: {r.status_code}")
    except:
        print("Connection Error")

if __name__ == "__main__":
    print("--- 🚀 NEW BOT STARTING 🚀 ---")
    
    # Check if the new bot can talk to you
    send_msg("💎 NEW BOT IS LIVE AND SCANNING!")

    while True:
        for m in MARKETS:
            print(f"Scanning {m}...")
        time.sleep(60)
