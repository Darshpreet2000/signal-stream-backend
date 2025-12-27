import requests
import time
import sys

def test_health():
    print("Testing health endpoint...")
    try:
        response = requests.get("http://localhost:8003/health")
        if response.status_code == 200:
            print("✅ Health check passed!")
            print(response.json())
            return True
        else:
            print(f"❌ Health check failed with status {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ Could not connect to server: {e}")
        return False

if __name__ == "__main__":
    # Wait for server to be ready
    for i in range(5):
        if test_health():
            sys.exit(0)
        print("Waiting for server...")
        time.sleep(2)
    sys.exit(1)
