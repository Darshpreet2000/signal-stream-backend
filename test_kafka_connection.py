#!/usr/bin/env python3
"""Test Kafka connectivity and credentials."""

import sys
from confluent_kafka import Producer, Consumer, KafkaException
from confluent_kafka.admin import AdminClient, NewTopic
import os
from dotenv import load_dotenv

load_dotenv()

def get_kafka_config():
    """Get Kafka configuration from environment."""
    return {
        'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS'),
        'security.protocol': os.getenv('KAFKA_SECURITY_PROTOCOL', 'SASL_SSL'),
        'sasl.mechanism': os.getenv('KAFKA_SASL_MECHANISM', 'PLAIN'),
        'sasl.username': os.getenv('KAFKA_API_KEY'),
        'sasl.password': os.getenv('KAFKA_API_SECRET'),
    }

def test_admin_connection():
    """Test admin client connection."""
    print("\n🔍 Testing Admin Client Connection...")
    print(f"   Bootstrap Servers: {os.getenv('KAFKA_BOOTSTRAP_SERVERS')}")
    print(f"   Security Protocol: {os.getenv('KAFKA_SECURITY_PROTOCOL')}")
    print(f"   SASL Mechanism: {os.getenv('KAFKA_SASL_MECHANISM')}")
    print(f"   API Key: {os.getenv('KAFKA_API_KEY')[:5]}***")
    
    try:
        config = get_kafka_config()
        admin = AdminClient(config)
        
        # Try to get cluster metadata
        print("\n📊 Fetching cluster metadata...")
        metadata = admin.list_topics(timeout=10)
        
        print(f"✅ Successfully connected to Kafka cluster!")
        print(f"   Cluster ID: {metadata.cluster_id}")
        print(f"   Broker count: {len(metadata.brokers)}")
        print(f"   Topic count: {len(metadata.topics)}")
        
        print("\n📋 Existing topics:")
        for topic_name in sorted(metadata.topics.keys()):
            if not topic_name.startswith('_'):  # Skip internal topics
                topic = metadata.topics[topic_name]
                print(f"   - {topic_name} ({len(topic.partitions)} partitions)")
        
        return True
        
    except KafkaException as e:
        print(f"\n❌ Kafka connection failed: {e}")
        print("\n💡 Troubleshooting steps:")
        print("   1. Verify your Confluent Cloud cluster is running")
        print("   2. Check if API key is still valid (they can expire)")
        print("   3. Ensure API key has proper ACL permissions")
        print("   4. Log in to https://confluent.cloud and verify credentials")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

def test_producer():
    """Test producer connection."""
    print("\n🔍 Testing Producer...")
    try:
        config = get_kafka_config()
        config.update({
            'client.id': 'test-producer',
        })
        
        producer = Producer(config)
        print("✅ Producer created successfully")
        
        # Flush to ensure connection works
        producer.flush(timeout=10)
        print("✅ Producer connection verified")
        
        return True
    except Exception as e:
        print(f"❌ Producer test failed: {e}")
        return False

def test_consumer():
    """Test consumer connection."""
    print("\n🔍 Testing Consumer...")
    try:
        config = get_kafka_config()
        config.update({
            'group.id': 'test-consumer-group',
            'auto.offset.reset': 'earliest',
        })
        
        consumer = Consumer(config)
        print("✅ Consumer created successfully")
        
        # Subscribe to test topic (won't create it)
        consumer.list_topics(timeout=10)
        print("✅ Consumer connection verified")
        
        consumer.close()
        return True
    except Exception as e:
        print(f"❌ Consumer test failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 Kafka Connectivity Test")
    print("=" * 60)
    
    results = {
        'admin': test_admin_connection(),
        'producer': test_producer(),
        'consumer': test_consumer(),
    }
    
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    print("=" * 60)
    for component, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {component.capitalize()}: {status}")
    
    print("=" * 60)
    
    if all(results.values()):
        print("\n✅ All tests passed! Kafka is configured correctly.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please check your configuration.")
        sys.exit(1)
