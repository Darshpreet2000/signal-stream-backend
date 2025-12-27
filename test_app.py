import requests
import json
import sys
import time
import uuid

BASE_URL = "http://localhost:8003"

def check_health():
    print(f"Checking health at {BASE_URL}/health...")
    for i in range(10):
        try:
            response = requests.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                print("✅ Server is healthy!")
                print(json.dumps(response.json(), indent=2))
                return True
            else:
                print(f"❌ Server returned {response.status_code}")
        except requests.exceptions.ConnectionError:
            print("⏳ Waiting for server to start...")
        
        time.sleep(2)
    
    print("❌ Server failed to start in time.")
    return False

def send_message(conversation_id):
    print(f"\nSending test message to {BASE_URL}/v1/messages...")
    payload = {
        "conversation_id": conversation_id,
        "sender": "customer",
        "message": "I am having trouble with my internet connection. It keeps dropping every few minutes.",
        "channel": "chat",
        "tenant_id": "demo-tenant"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/v1/messages", json=payload)
        if response.status_code == 202:
            print("✅ Message accepted!")
            print(json.dumps(response.json(), indent=2))
            return True
        else:
            print(f"❌ Failed to send message: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return False

def get_insights(conversation_id):
    print(f"\nPolling for insights at {BASE_URL}/v1/conversations/{conversation_id}/insights...")
    
    # Poll for up to 90 seconds
    for i in range(45):
        try:
            response = requests.get(f"{BASE_URL}/v1/conversations/{conversation_id}/insights")
            if response.status_code == 200:
                print("✅ Insights generated!")
                print(json.dumps(response.json(), indent=2))
                return True
            elif response.status_code == 404:
                print("⏳ Insights not ready yet...")
            else:
                print(f"❌ Error fetching insights: {response.status_code}")
                print(response.text)
        except Exception as e:
            print(f"❌ Error connecting: {e}")
        
        time.sleep(2)
        
    print("❌ Timed out waiting for insights.")
    return False

if __name__ == "__main__":
    if not check_health():
        sys.exit(1)
        
    conversation_id = str(uuid.uuid4())
    print(f"\nTest Conversation ID: {conversation_id}")
    
    if send_message(conversation_id):
        # Wait a bit for Kafka processing
        time.sleep(2)
        get_insights(conversation_id)
    else:
        print("\n❌ Test failed.")
        sys.exit(1)
