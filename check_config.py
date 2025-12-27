
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.config.settings import get_settings

def check_config():
    try:
        settings = get_settings()
        print("--- Kafka Configuration ---")
        print(f"KAFKA_ENABLED: {settings.kafka_enabled}")
        print(f"KAFKA_BOOTSTRAP_SERVERS: {settings.kafka_bootstrap_servers}")
        print(f"KAFKA_SECURITY_PROTOCOL: {settings.kafka_security_protocol}")
        print(f"KAFKA_SASL_MECHANISM: {settings.kafka_sasl_mechanism}")
        
        # Mask secrets
        api_key = settings.kafka_api_key or settings.kafka_sasl_username
        api_secret = settings.kafka_api_secret or settings.kafka_sasl_password
        
        print(f"KAFKA_API_KEY: {'*' * 4 + api_key[-4:] if api_key and len(api_key) > 4 else 'NOT SET'}")
        print(f"KAFKA_API_SECRET: {'*' * 4 + api_secret[-4:] if api_secret and len(api_secret) > 4 else 'NOT SET'}")
        
        print("\n--- Gemini Configuration ---")
        print(f"GEMINI_API_KEY: {'*' * 4 + settings.gemini_api_key[-4:] if settings.gemini_api_key and len(settings.gemini_api_key) > 4 else 'NOT SET'}")

    except Exception as e:
        print(f"Error loading settings: {e}")

if __name__ == "__main__":
    check_config()
