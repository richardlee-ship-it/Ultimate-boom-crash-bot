import requests

# Test credentials
TOKEN = "8667543667:AAFFdhIPIjJGAVcbQ3be8wYgQQNvy_5mB9s"
CHAT_ID = "6856488919"

def run_test():
    print("--- STARTING ONE-TIME CONNECTION TEST ---")
    url = f"https://api.telegram.org/bot{TOKEN}/getMe"
    
    try:
        # Test 1: Check if the token is even valid
        r1 = requests.get(url)
        print(f"Test 1 (Token Check) Status: {r1.status_code}")
        print(f"Response: {r1.text}")
        
        # Test 2: Try to send a message
        msg_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": "🚨 TEST CODE WORKING!"}
        r2 = requests.post(msg_url, json=payload)
        print(f"Test 2 (Message Send) Status: {r2.status_code}")
        
    except Exception as e:
        print(f"Connection Error: {e}")

if __name__ == "__main__":
    run_test()
