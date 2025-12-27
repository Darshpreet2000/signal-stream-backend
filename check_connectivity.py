
import socket
import sys

def check_connection(host, port):
    print(f"Checking connection to {host}:{port}...")
    try:
        sock = socket.create_connection((host, port), timeout=5)
        print("✅ Connection successful!")
        sock.close()
        return True
    except socket.error as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    host = "pkc-619z3.us-east1.gcp.confluent.cloud"
    port = 9092
    check_connection(host, port)
