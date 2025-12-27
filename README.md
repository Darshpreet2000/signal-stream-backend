# SignalStream AI Backend

**Real-time Support Intelligence Platform powered by Confluent Cloud and Google Gemini AI**

[![Confluent Cloud](https://img.shields.io/badge/Confluent-Cloud-blue?logo=apache-kafka)](https://confluent.cloud)
[![Schema Registry](https://img.shields.io/badge/Schema-Registry-green)](https://docs.confluent.io/platform/current/schema-registry)
[![Google Gemini](https://img.shields.io/badge/Google-Gemini%20AI-orange?logo=google)](https://ai.google.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-teal?logo=fastapi)](https://fastapi.tiangolo.com)

## Overview

SignalStream AI is a **production-grade streaming platform** that provides real-time intelligence for customer support conversations. Built for the [Google Cloud AI Partner Catalyst Hackathon](https://ai-partner-catalyst.devpost.com/) (**Confluent Challenge**), it demonstrates advanced event-driven architecture with:

- 🎯 **Confluent Cloud** - Managed Kafka with SASL_SSL security
- 📋 **Schema Registry with Avro** - Type-safe message contracts with 30-50% size reduction
- 🤖 **Google Gemini AI** - 4 parallel AI agents (sentiment, PII, insights, summary)
- ⚡ **Real-time Processing** - Sub-second latency from message to intelligence
- 🔄 **Event-Driven Architecture** - 6 Kafka consumers, 7 topics, DLQ pattern

### Why Schema Registry Matters

This project implements **7 production-grade Avro schemas** for all message types:
- ✅ **Type Safety** - Contract validation at serialization time
- ✅ **Smaller Payloads** - 30-50% message size reduction vs JSON
- ✅ **Schema Evolution** - Backward/forward compatibility for versioning
- ✅ **Self-Documenting** - Schemas serve as living API contracts

**Automatic Fallback**: If Schema Registry isn't configured, the system seamlessly falls back to JSON serialization—demonstrating graceful degradation for production systems.

### Key Features

- **Sentiment Analysis** - Detect customer emotions with confidence scoring
- **PII Detection** - Identify and flag personally identifiable information  
- **Intent Extraction** - Understand customer needs and urgency levels
- **Conversation Summarization** - Generate concise TL;DR automatically
- **WebSocket Streaming** - Real-time intelligence delivery to dashboards

For an end-to-end walkthrough of how messages flow through FastAPI → Kafka → AI agents → aggregation → WebSockets, see `PROJECT_OVERVIEW.md` (section: **Backend Project Flow (Detailed)**).

### Architecture

```
┌─────────────────┐
│  Customer Apps  │ ──► POST /v1/messages
└─────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│          Kafka (Confluent Cloud)        │
│  ┌──────────┐  ┌──────────────────────┐│
│  │ Messages │─▶│ Conversation State   ││
│  │   Raw    │  │                      ││
│  └──────────┘  └──────────────────────┘│
│                         │               │
│         ┌───────────────┼───────────────┼────────┐
│         ▼               ▼               ▼        ▼
│  ┌──────────┐  ┌─────┐  ┌─────┐  ┌──────────┐  │
│  │Sentiment │  │ PII │  │Insig│  │ Summary  │  │
│  │  Agent   │  │Agent│  │Agent│  │  Agent   │  │
│  └──────────┘  └─────┘  └─────┘  └──────────┘  │
│         │               │               │        │
│         └───────────────┼───────────────┘        │
│                         ▼                        │
│                  ┌──────────────┐                │
│                  │  Aggregated  │                │
│                  │ Intelligence │                │
│                  └──────────────┘                │
└─────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│   FastAPI APIs  │ ──► GET /v1/conversations/{id}/insights
│   + WebSockets  │ ──► ws://.../{id}/stream
└─────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- Confluent Cloud account (free tier available)
- Google Cloud account with Gemini API access

### 1. Clone and Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Required configuration:
- `KAFKA_BOOTSTRAP_SERVERS` - Your Confluent Cloud bootstrap servers
- `KAFKA_API_KEY` - Confluent Cloud API key
- `KAFKA_API_SECRET` - Confluent Cloud API secret
- `GEMINI_API_KEY` - Your Google Gemini API key

**Optional (Advanced):**
- `KAFKA_SCHEMA_REGISTRY_URL` - Enable Avro serialization with Schema Registry
- `KAFKA_SCHEMA_REGISTRY_API_KEY` - Schema Registry API key
- `KAFKA_SCHEMA_REGISTRY_API_SECRET` - Schema Registry API secret

> **💡 Schema Registry Integration**: When configured, messages are automatically serialized with Avro for type safety and backward compatibility. See [SCHEMA_REGISTRY.md](./SCHEMA_REGISTRY.md) for details.

Legacy env vars are still supported (deprecated): `KAFKA_SASL_USERNAME`, `KAFKA_SASL_PASSWORD`.

If you want to run the backend **without Confluent/Kafka** (demo/dev mode), set:

- `KAFKA_ENABLED=false`

In this mode, the `/v1/messages` endpoint skips Kafka publishing and uses the in-process development shortcut for generating intelligence and AI replies.

### 3. Run the Application

#### Quick Start

```bash
# Use the convenient start script
./start.sh
```

#### Manual Start

```bash
# Activate virtual environment
source venv/bin/activate

# Run the application
python run.py

# Or with uvicorn directly
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### 4. Test the Application

```bash
# Run comprehensive API tests
./test.sh

# Or run directly with Python
source venv/bin/activate
python test_api.py
```

The test script will:
1. Check API health
2. Send dummy conversation messages
3. Verify AI intelligence generation
4. Test WebSocket streaming
5. Provide a detailed test report

## API Reference

### Producer API - Message Ingestion

#### POST /v1/messages

Ingest a support message into the platform.

**Request:**
```json
{
  "conversation_id": "conv_12345",
  "sender": "customer",
  "message": "I'm having trouble with my recent order",
  "channel": "chat",
  "tenant_id": "acme-corp"
}
```

**Response (202 Accepted):**
```json
{
  "message_id": "550e8400-e29b-41d4-a716-446655440000",
  "conversation_id": "conv_12345",
  "status": "accepted",
  "timestamp": "2025-12-25T10:30:00Z"
}
```

### Consumer API - Intelligence Retrieval

#### GET /v1/conversations/{conversation_id}/insights

Get the latest AI-generated intelligence for a conversation.

**Response (200 OK):**
```json
{
  "conversation_id": "conv_12345",
  "tenant_id": "acme-corp",
  "sentiment": {
    "sentiment": "negative",
    "confidence": 0.87,
    "emotion": "frustrated",
    "reasoning": "Customer expressing dissatisfaction"
  },
  "pii": {
    "has_pii": true,
    "entities": [{"type": "email", "value": "[REDACTED]"}]
  },
  "insights": {
    "intent": "refund_request",
    "urgency": "high",
    "suggested_actions": ["Apologize", "Process refund"],
    "requires_escalation": false
  },
  "summary": {
    "tldr": "Customer requesting refund for order #12345",
    "customer_issue": "Wrong item received",
    "follow_up_needed": true
  }
}
```

### WebSocket API - Real-time Streaming

#### ws://localhost:8000/ws/conversations/{conversation_id}/stream

Subscribe to real-time intelligence updates for a conversation.

**Connection Message:**
```json
{
  "type": "connected",
  "conversation_id": "conv_12345",
  "message": "Connected to conversation stream"
}
```

**Intelligence Update:**
```json
{
  "type": "intelligence_update",
  "conversation_id": "conv_12345",
  "data": { ...aggregated_intelligence... }
}
```

## Customer Onboarding Guide

### For Customers Integrating SignalStream AI

#### Step 1: Get Credentials

Contact SignalStream to obtain your:
- `tenant_id` - Your unique tenant identifier
- API endpoint - Production API base URL

#### Step 2: Send Messages

Integrate the message ingestion endpoint into your support application:

```python
import requests

response = requests.post(
    "https://api.signalstream.ai/v1/messages",
    json={
        "conversation_id": "your-conversation-id",
        "sender": "customer",
        "message": "Customer message text",
        "channel": "chat",
        "tenant_id": "your-tenant-id"
    }
)
```

#### Step 3: Receive Intelligence

Poll for intelligence or establish WebSocket connection:

```python
# Polling
response = requests.get(
    f"https://api.signalstream.ai/v1/conversations/{conversation_id}/insights",
    params={"tenant_id": "your-tenant-id"}
)
intelligence = response.json()

# WebSocket (Python example)
import websockets

async with websockets.connect(
    f"wss://api.signalstream.ai/ws/conversations/{conversation_id}/stream"
) as websocket:
    while True:
        update = await websocket.recv()
        print(f"Intelligence update: {update}")
```

## Development

### Project Structure

```
backend/
├── src/
│   ├── api/              # FastAPI routers
│   │   ├── messages.py   # Message ingestion endpoint
│   │   ├── conversations.py  # Intelligence retrieval
│   │   ├── websocket.py  # Real-time streaming
│   │   └── health.py     # Health checks
│   ├── ai/               # AI services
│   │   └── gemini_service.py  # Gemini integration
│   ├── kafka/            # Kafka infrastructure
│   │   ├── producer.py   # Kafka producer
│   │   ├── consumer.py   # Base consumer
│   │   └── admin.py      # Topic management
│   ├── consumers/        # AI agent consumers
│   │   ├── sentiment_agent.py
│   │   ├── pii_agent.py
│   │   ├── insights_agent.py
│   │   ├── summary_agent.py
│   │   └── aggregation_consumer.py
│   ├── models/           # Pydantic models
│   ├── config/           # Configuration
│   └── main.py           # FastAPI application
├── requirements.txt
├── pyproject.toml
└── .env.example
```

### Running Tests

```bash
pytest tests/ -v
```

### Code Quality

```bash
# Format code
black src/

# Lint code
ruff check src/

# Type checking
mypy src/
```

## Confluent Cloud Setup

### 1. Create Cluster

1. Sign up at https://confluent.cloud
2. Create a new Basic cluster (free tier available)
3. Note your bootstrap servers

### 2. Create API Keys

1. Go to Cluster → API Keys
2. Create new API key with Global access
3. Save the key and secret

### 3. Topics

The application automatically creates these topics:
- `support.messages.raw` - Incoming messages
- `support.conversations.state` - Conversation context
- `support.ai.sentiment` - Sentiment analysis results
- `support.ai.pii` - PII detection results
- `support.ai.insights` - Intent/insights
- `support.ai.summary` - Summaries
- `support.ai.aggregated` - Combined intelligence
- `support.dlq` - Dead letter queue

## Google Gemini Setup

### 1. Get API Key

1. Go to https://aistudio.google.com/app/apikey
2. Create new API key
3. Copy the key to your `.env` file

### 2. Model Configuration

The default model is `gemini-1.5-pro`. You can change this in `.env`:

```bash
GEMINI_MODEL=gemini-1.5-pro
GEMINI_TEMPERATURE=0.3
GEMINI_MAX_OUTPUT_TOKENS=2048
```

## Deployment

### Docker

```bash
docker build -t signalstream-backend .
docker run -p 8000:8000 --env-file .env signalstream-backend
```

### Kubernetes

See `k8s/` directory for Kubernetes manifests.

## Monitoring

### Health Endpoints

- `GET /health` - Overall health status
- `GET /ready` - Readiness probe
- `GET /live` - Liveness probe

### Metrics

Metrics are available at `:9090/metrics` (if enabled).

## Security Considerations

- **Multi-Tenancy**: All data is isolated by `tenant_id`
- **PII Detection**: Automatically flags sensitive information
- **Kafka ACLs**: Configure Confluent Cloud ACLs for production
- **API Authentication**: Add JWT/OAuth2 for production use

## Troubleshooting

### Kafka Connection Issues

```bash
# Test Kafka connectivity
kafka-console-producer --broker-list $KAFKA_BOOTSTRAP_SERVERS \
  --producer.config client.properties \
  --topic test
```

### Consumer Not Processing

Check logs for:
- Consumer group lag
- Gemini API rate limits
- Topic subscription issues

### Performance Tuning

- Increase `max_concurrent_ai_requests` for higher throughput
- Adjust Kafka consumer `max.poll.interval.ms`
- Scale horizontally by adding more consumer instances

## License

Proprietary - SignalStream AI

## Support

- Documentation: https://docs.signalstream.ai
- Email: support@signalstream.ai
- Slack: signalstream.slack.com
