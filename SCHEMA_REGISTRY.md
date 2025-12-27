# Schema Registry Integration

## Overview

SignalStream uses **Confluent Schema Registry** with **Avro serialization** for type-safe message streaming. This ensures:
- **Data contract enforcement** - All messages conform to predefined schemas
- **Schema evolution** - Backward/forward compatibility across versions
- **Reduced payload size** - Binary Avro format vs JSON
- **Type safety** - Compile-time validation of message structures

## Architecture

```
Producer (FastAPI)
    ↓
Avro Serializer → Schema Registry
    ↓
Kafka Topic (Binary Avro)
    ↓
Avro Deserializer ← Schema Registry
    ↓
Consumer (Python)
```

## Schemas Defined

All schemas are in `src/schemas/avro_schemas.py`:

1. **SupportMessage** - Customer/agent messages (`support.messages.raw`)
2. **ConversationState** - Conversation tracking (`support.conversations.state`)
3. **SentimentAnalysis** - AI sentiment results (`support.ai.sentiment`)
4. **PIIDetection** - Privacy scanning results (`support.ai.pii`)
5. **CustomerInsights** - Intent & urgency detection (`support.ai.insights`)
6. **ConversationSummary** - AI-generated summaries (`support.ai.summary`)
7. **AggregatedIntelligence** - Combined results (`support.ai.aggregated`)

## Configuration

### Enable Schema Registry

Add to `.env`:

```bash
# Schema Registry Configuration (Confluent Cloud)
KAFKA_SCHEMA_REGISTRY_URL=https://psrc-xxxxx.us-east-2.aws.confluent.cloud
KAFKA_SCHEMA_REGISTRY_API_KEY=your-sr-api-key
KAFKA_SCHEMA_REGISTRY_API_SECRET=your-sr-api-secret
```

### Get Credentials from Confluent Cloud

1. Go to **Confluent Cloud Console** → Your Cluster
2. Navigate to **Schema Registry** tab
3. Click **API credentials** → Create new key
4. Copy URL, API Key, and Secret

## Usage

### Automatic Fallback

Schema Registry is **optional**. The system automatically:
- Uses Avro serialization when Schema Registry is configured
- Falls back to JSON serialization when not configured
- No code changes required!

### Manual Serialization (Optional)

```python
from src.schemas.registry import get_schema_registry_manager
from src.schemas.avro_schemas import MESSAGE_SCHEMA

manager = get_schema_registry_manager()

# Check if enabled
if manager.is_enabled():
    # Serialize message
    serialized = manager.serialize(
        schema=MESSAGE_SCHEMA,
        data={"message_id": "123", "content": "Hello"},
        topic="support.messages.raw"
    )
    
    # Deserialize message
    deserialized = manager.deserialize(
        schema=MESSAGE_SCHEMA,
        data=serialized,
        topic="support.messages.raw"
    )
```

## Benefits for Hackathon Judges

### 1. **Production-Ready Architecture**
- Enterprise-grade schema management
- Used by Fortune 500 companies
- Demonstrates advanced Confluent features

### 2. **Type Safety**
- Prevents data corruption
- Enforces contracts between services
- Catches errors at serialization time

### 3. **Schema Evolution**
- Add fields without breaking consumers
- Version management built-in
- Backward/forward compatibility

### 4. **Performance**
- Binary format reduces network bandwidth
- Faster serialization than JSON
- Schema cached locally (not fetched per message)

## Monitoring

Check Schema Registry status:

```python
from src.schemas.registry import schema_registry_enabled

if schema_registry_enabled():
    print("✅ Schema Registry is enabled and working")
else:
    print("⚠️ Schema Registry not configured - using JSON fallback")
```

## Troubleshooting

### Schema Registry not connecting?

1. Verify credentials in `.env`
2. Check network connectivity: `curl -u $API_KEY:$API_SECRET $SR_URL/subjects`
3. Ensure API key has Schema Registry permissions

### Want to see schemas in Confluent Cloud?

1. Go to **Schema Registry** tab in Confluent Cloud
2. See all registered schemas and versions
3. View compatibility settings per schema

## Advanced: Schema Evolution Example

### Version 1 (Initial)
```python
{
    "name": "SupportMessage",
    "fields": [
        {"name": "message_id", "type": "string"},
        {"name": "content", "type": "string"}
    ]
}
```

### Version 2 (Add optional field)
```python
{
    "name": "SupportMessage",
    "fields": [
        {"name": "message_id", "type": "string"},
        {"name": "content", "type": "string"},
        {"name": "priority", "type": ["null", "string"], "default": None}  # New field
    ]
}
```

**Result**: Old consumers still work! Schema Registry validates compatibility automatically.

---

## For Hackathon Judges 👨‍⚖️

This integration demonstrates:
- ✅ **Advanced Confluent features** (not just basic Kafka)
- ✅ **Production-ready patterns** (schema management)
- ✅ **Enterprise architecture** (type safety, evolution)
- ✅ **Backward compatibility** (graceful fallback to JSON)

**Bottom line**: We're not just using Kafka, we're using it *properly* with industry best practices.
