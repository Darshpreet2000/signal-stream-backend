#!/usr/bin/env python
"""
Script to verify Kafka topics exist in Confluent Cloud
"""

import sys
from confluent_kafka.admin import AdminClient, ConfigResource
from src.config import get_settings


def check_topics():
    """Check if all required topics exist in Confluent Cloud."""
    print("🔍 Checking Confluent Cloud Topics...")
    print("=" * 70)
    
    settings = get_settings()
    
    # Kafka admin configuration
    admin_config = {
        'bootstrap.servers': settings.kafka_bootstrap_servers,
        'security.protocol': settings.kafka_security_protocol,
        'sasl.mechanisms': settings.kafka_sasl_mechanism,
        'sasl.username': settings.kafka_api_key_effective,
        'sasl.password': settings.kafka_api_secret_effective,
        'socket.timeout.ms': 10000,
        'api.version.request.timeout.ms': 10000,
    }
    
    print(f"\n📡 Connecting to: {settings.kafka_bootstrap_servers}")
    masked = (settings.kafka_api_key_effective[:4] + "…") if settings.kafka_api_key_effective else "<empty>"
    print(f"🔐 Using Kafka API key: {masked}")
    
    try:
        admin_client = AdminClient(admin_config)
        
        print("\n⏳ Fetching cluster metadata (this may take a moment)...")
        
        # Get cluster metadata with timeout
        metadata = admin_client.list_topics(timeout=30)
        
        print(f"\n✅ Successfully connected to Confluent Cloud!")
        print(f"📊 Cluster has {len(metadata.topics)} total topics")
        
        # Expected topics for our application
        expected_topics = [
            settings.kafka_topic_messages_raw,
            settings.kafka_topic_conversations_state,
            settings.kafka_topic_ai_sentiment,
            settings.kafka_topic_ai_pii,
            settings.kafka_topic_ai_insights,
            settings.kafka_topic_ai_summary,
            settings.kafka_topic_ai_aggregated,
            settings.kafka_topic_dlq,
        ]
        
        print(f"\n🔎 Checking for {len(expected_topics)} required topics:")
        print("-" * 70)
        
        found_topics = []
        missing_topics = []
        
        for topic_name in expected_topics:
            if topic_name in metadata.topics:
                topic_metadata = metadata.topics[topic_name]
                partition_count = len(topic_metadata.partitions)
                found_topics.append(topic_name)
                print(f"✅ {topic_name:<40} ({partition_count} partitions)")
            else:
                missing_topics.append(topic_name)
                print(f"❌ {topic_name:<40} (NOT FOUND)")
        
        print("\n" + "=" * 70)
        print(f"📈 Summary: {len(found_topics)}/{len(expected_topics)} topics found")
        
        if missing_topics:
            print(f"\n⚠️  Missing topics: {', '.join(missing_topics)}")
            print("\n💡 To create missing topics, start the backend application:")
            print("   ./start.sh")
            return False
        else:
            print("\n🎉 All required topics exist in Confluent Cloud!")
            print("✅ Your cluster is ready for the SignalStream AI backend")
            return True
            
    except Exception as e:
        print(f"\n❌ Error connecting to Confluent Cloud: {e}")
        print("\n🔧 Troubleshooting:")
        print("  1. Verify your network can reach Confluent Cloud")
        print("  2. Check credentials in .env file")
        print("  3. Ensure your Confluent Cloud cluster is active")
        print(f"  4. Try: telnet {settings.kafka_bootstrap_servers.split(':')[0]} 9092")
        return False


def list_all_topics():
    """List all topics in the cluster."""
    print("\n" + "=" * 70)
    print("📋 ALL TOPICS IN CLUSTER")
    print("=" * 70)
    
    settings = get_settings()
    admin_config = {
        'bootstrap.servers': settings.kafka_bootstrap_servers,
        'security.protocol': settings.kafka_security_protocol,
        'sasl.mechanisms': settings.kafka_sasl_mechanism,
        'sasl.username': settings.kafka_api_key_effective,
        'sasl.password': settings.kafka_api_secret_effective,
        'socket.timeout.ms': 10000,
    }
    
    try:
        admin_client = AdminClient(admin_config)
        metadata = admin_client.list_topics(timeout=30)
        
        topics = sorted(metadata.topics.keys())
        
        for topic_name in topics:
            topic_metadata = metadata.topics[topic_name]
            partition_count = len(topic_metadata.partitions)
            print(f"  • {topic_name} ({partition_count} partitions)")
        
        print(f"\nTotal: {len(topics)} topics")
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    try:
        success = check_topics()
        
        if len(sys.argv) > 1 and sys.argv[1] == "--all":
            list_all_topics()
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Check interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
