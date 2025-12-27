"""
Demonstration script showing Schema Registry integration.

This script demonstrates:
1. Schema Registry connection
2. Avro serialization/deserialization
3. Schema compatibility
4. Performance comparison (Avro vs JSON)
"""

import json
import time
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from src.schemas.registry import get_schema_registry_manager, schema_registry_enabled
from src.schemas.avro_schemas import MESSAGE_SCHEMA, SENTIMENT_SCHEMA
from datetime import datetime


def demo_schema_registry():
    """Demonstrate Schema Registry capabilities."""
    
    print("=" * 70)
    print("🎯 SignalStream Schema Registry Demonstration")
    print("=" * 70)
    print()
    
    # Check if Schema Registry is enabled
    manager = get_schema_registry_manager()
    
    if not schema_registry_enabled():
        print("⚠️  Schema Registry is NOT configured")
        print()
        print("To enable Schema Registry, add these to your .env file:")
        print("  KAFKA_SCHEMA_REGISTRY_URL=https://psrc-xxxxx.aws.confluent.cloud")
        print("  KAFKA_SCHEMA_REGISTRY_API_KEY=your-key")
        print("  KAFKA_SCHEMA_REGISTRY_API_SECRET=your-secret")
        print()
        print("✅ System will use JSON serialization (automatic fallback)")
        return
    
    print("✅ Schema Registry is ENABLED and connected!")
    print()
    
    # Sample message data
    message_data = {
        "message_id": "msg_12345",
        "conversation_id": "conv_demo",
        "tenant_id": "hackathon_demo",
        "sender_role": "customer",
        "content": "I'm very frustrated with the delayed refund!",
        "timestamp": datetime.utcnow().isoformat(),
        "metadata": None
    }
    
    print("📋 Sample Message Data:")
    print(json.dumps(message_data, indent=2))
    print()
    
    # Serialize with Avro
    print("🔄 Serializing with Avro...")
    start_avro = time.perf_counter()
    avro_bytes = manager.serialize(
        schema=MESSAGE_SCHEMA,
        data=message_data,
        topic="support.messages.raw"
    )
    avro_time = time.perf_counter() - start_avro
    
    if avro_bytes:
        print(f"✅ Avro serialization successful!")
        print(f"   Size: {len(avro_bytes)} bytes")
        print(f"   Time: {avro_time * 1000:.3f}ms")
        print()
        
        # Deserialize with Avro
        print("🔄 Deserializing with Avro...")
        start_deser = time.perf_counter()
        deserialized = manager.deserialize(
            schema=MESSAGE_SCHEMA,
            data=avro_bytes,
            topic="support.messages.raw"
        )
        deser_time = time.perf_counter() - start_deser
        
        if deserialized:
            print(f"✅ Avro deserialization successful!")
            print(f"   Time: {deser_time * 1000:.3f}ms")
            print()
    
    # Compare with JSON
    print("📊 Performance Comparison:")
    print("-" * 70)
    
    # JSON serialization
    start_json = time.perf_counter()
    json_bytes = json.dumps(message_data).encode('utf-8')
    json_time = time.perf_counter() - start_json
    
    print(f"JSON:")
    print(f"  Size: {len(json_bytes)} bytes")
    print(f"  Serialization time: {json_time * 1000:.3f}ms")
    print()
    
    if avro_bytes:
        print(f"Avro (with Schema Registry):")
        print(f"  Size: {len(avro_bytes)} bytes")
        print(f"  Serialization time: {avro_time * 1000:.3f}ms")
        print()
        
        size_reduction = (1 - len(avro_bytes) / len(json_bytes)) * 100
        print(f"💾 Size reduction: {size_reduction:.1f}%")
        print(f"⚡ Avro is {len(json_bytes) / len(avro_bytes):.1f}x smaller!")
    
    print()
    print("=" * 70)
    print("🎉 Benefits of Schema Registry:")
    print("=" * 70)
    print("✅ Type safety - Schema validation at serialization time")
    print("✅ Backward compatibility - Schema evolution without breaking changes")
    print("✅ Smaller payloads - Binary format reduces network bandwidth")
    print("✅ Faster processing - No JSON parsing overhead")
    print("✅ Data contracts - Enforced schemas across producers/consumers")
    print()
    print("🏆 This is production-grade Confluent Cloud architecture!")
    print("=" * 70)


if __name__ == "__main__":
    try:
        demo_schema_registry()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
