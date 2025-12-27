
from confluent_kafka.admin import AdminClient
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))
from src.config.settings import get_settings

def test_admin_client():
    settings = get_settings()
    
    conf = {
        'bootstrap.servers': settings.kafka_bootstrap_servers,
        'security.protocol': settings.kafka_security_protocol,
        'sasl.mechanism': settings.kafka_sasl_mechanism,
        'sasl.username': settings.kafka_api_key,
        'sasl.password': settings.kafka_api_secret,
        'ssl.ca.location': '/etc/ssl/cert.pem',
        # 'debug': 'all',  # Enable debug logging
    }
    
    print("Creating AdminClient with config:")
    print(f"bootstrap.servers: {conf['bootstrap.servers']}")
    print(f"security.protocol: {conf['security.protocol']}")
    print(f"sasl.mechanism: {conf['sasl.mechanism']}")
    
    try:
        admin_client = AdminClient(conf)
        print("AdminClient created. Listing topics...")
        metadata = admin_client.list_topics(timeout=10)
        print(f"Topics: {list(metadata.topics.keys())}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_admin_client()
