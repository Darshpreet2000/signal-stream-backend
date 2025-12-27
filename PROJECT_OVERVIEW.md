# SignalStream AI Backend - Project Overview

## 🎯 What We Built

A **production-grade, event-driven streaming platform** that provides real-time AI intelligence for customer support conversations using:

- **Confluent Kafka** - Event streaming backbone
- **Google Gemini AI** - Multi-agent AI processing
- **FastAPI** - Modern Python async API framework
- **WebSockets** - Real-time streaming updates

## 🏗️ Architecture

## 🧭 Backend Project Flow (Detailed)

This section explains the backend flow end-to-end: how the FastAPI app boots, how messages move through Kafka + AI agents, how results are aggregated, and how the UI receives updates.

### 1) Startup & Application State

**Entry point**: `src/main.py`

On startup, the app initializes core services and attaches them to `app.state` so they can be reused by API handlers and background workers:

- `app.state.gemini_service`: Gemini client wrapper (`src/ai/gemini_service.py`)
- `app.state.producer`: Kafka producer (`src/kafka/producer.py`)
- `app.state.intelligence_cache`: in-memory store of latest aggregated intelligence per `(tenant_id, conversation_id)`
- `app.state.local_conversation_messages`: development-only local message history used by the “dev shortcut” in the message ingestion endpoint

**Kafka initialization** runs in the background so the HTTP server becomes available immediately:

1. Kafka Admin verifies topics exist.
2. Kafka Producer initializes.
3. Kafka Consumers start (conversation processor, agents, aggregator).

If Kafka is unavailable/slow, the backend still stays responsive in **development mode** by computing intelligence directly inside the message endpoint (see section 3).

### 2) HTTP & WebSocket Surface Area

Routers are wired in `src/main.py`:

- **Health**: `GET /health` (no version prefix)
- **Message ingestion (Producer API)**: `POST /{api_version}/messages`
- **Intelligence retrieval (Consumer API)**: `GET /{api_version}/conversations/{conversation_id}/insights`
- **WebSocket streaming**: `WS /ws/conversations/{conversation_id}/stream` (no version prefix)

The frontend uses these endpoints via its API client (typically through a reverse proxy path like `/api`).

### 3) Message Ingestion Flow (POST /v1/messages)

**Handler**: `src/api/messages.py:create_message`

When a message is posted:

1. The handler generates a `message_id` and resolves `tenant_id`.
2. It builds a `SupportMessage` Pydantic object.
3. It publishes the message to Kafka topic `support.messages.raw`.

#### Development-mode shortcut

When `APP_ENV=development`, the endpoint also performs an in-process compute path to keep the demo responsive:

- Maintains a local conversation transcript in `app.state.local_conversation_messages` keyed by `{tenant_id}:{conversation_id}`.
- Runs Gemini calls to produce:
  - sentiment (`analyze_sentiment`)
  - pii (`detect_pii`)
  - insights (`extract_insights`)
  - summary (`summarize_conversation`)
- Writes the resulting `AggregatedIntelligence` into `app.state.intelligence_cache`.
- Broadcasts the intelligence update via WebSocket to any subscribers.

Additionally, for **customer** messages, the endpoint generates an **AI chat reply** via `GeminiService.generate_response(...)` and returns it on the HTTP response as `ai_response`.

This means the demo can show:

- An immediate AI reply in the chat pane (HTTP response)
- Real-time intelligence updates in the dashboard pane (WebSocket push)

### 4) Kafka Pipeline (Production-Style Path)

In non-development environments (or when you want the full streaming path), the primary flow is:

#### A) Conversation state builder

**Consumer**: `src/consumers/conversation_processor.py:ConversationProcessorConsumer`

- Consumes `support.messages.raw`
- Parses the raw `SupportMessage`
- Updates an in-memory `ConversationState` (keyed by `{tenant_id}:{conversation_id}`)
- Produces `ConversationState` to `support.conversations.state`

#### B) AI agents (parallel)

Each agent consumes the conversation state topic and emits its own result:

- Sentiment Agent: `src/consumers/sentiment_agent.py` → `support.ai.sentiment`
- PII Agent: `src/consumers/pii_agent.py` → `support.ai.pii`
- Insights Agent: `src/consumers/insights_agent.py` → `support.ai.insights`
- Summary Agent: `src/consumers/summary_agent.py` → `support.ai.summary`

Each agent typically uses the most recent message (or a short context window) and calls Gemini through `src/ai/gemini_service.py`.

#### C) Aggregation

**Consumer**: `src/consumers/aggregation_consumer.py:AggregationConsumer`

- Consumes all agent topics
- Infers which result type arrived (sentiment/pii/insights/summary) by schema shape
- Merges the newest partial result into a single `AggregatedIntelligence` object per conversation
- Produces the aggregated object to `support.ai.aggregated`
- Broadcasts the newest aggregate to WebSocket subscribers

### 5) Intelligence Retrieval (GET /v1/conversations/{id}/insights)

**Handler**: `src/api/conversations.py:get_conversation_insights`

- Reads the latest value from `app.state.intelligence_cache` using key `{tenant_id}:{conversation_id}`
- If not present, returns 404 (“not yet processed”)

Note: In this demo architecture, `intelligence_cache` is in memory. In production you’d typically replace this with Redis or a database.

### 6) Real-time Streaming (WebSocket)

**Endpoint**: `src/api/websocket.py:websocket_conversation_stream`

- Clients connect per conversation ID
- The server tracks active connections per conversation
- `broadcast_intelligence(conversation_id, intelligence)` pushes JSON snapshots whenever new intelligence is computed (dev shortcut) or aggregated (Kafka path)

### 7) Error Handling & DLQ Pattern

**Base consumer**: `src/kafka/consumer.py:BaseKafkaConsumer`

- Parses Kafka message value + headers
- Retries processing with exponential backoff up to `max_retries`
- On final failure, sends the message to `support.dlq` if a producer is configured

### 8) Observability (Logs)

The backend logs show:

- Request-level traces for message ingestion (including dev shortcut steps)
- Gemini calls and summarized results
- Kafka produce events and consumer processing lifecycle
- WebSocket connect/disconnect and broadcast statistics

In development the log level is **DEBUG**, and in production it defaults to **INFO**.

### Event-Driven Flow

```
Customer App
     │
     ▼
[POST /v1/messages] ───► [Kafka: support.messages.raw]
                                      │
                                      ▼
                        [Conversation Processor Consumer]
                                      │
                                      ▼
                    [Kafka: support.conversations.state]
                                      │
         ┌────────────────────────────┼─────────────────────────┐
         │                            │                          │
         ▼                            ▼                          ▼
[Sentiment Agent]            [PII Agent]               [Insights Agent]
         │                            │                          │
         ▼                            ▼                          ▼
[support.ai.sentiment]    [support.ai.pii]        [support.ai.insights]
         │                            │                          │
         └────────────────────────────┼──────────────────────────┘
                                      ▼
                         [Aggregation Consumer]
                                      │
                                      ▼
                   [Kafka: support.ai.aggregated]
                                      │
         ┌────────────────────────────┴──────────────────────────┐
         ▼                                                        ▼
[GET /v1/conversations/:id/insights]         [WebSocket: ws://.../stream]
         │                                                        │
         ▼                                                        ▼
  [Polling Client]                                    [Real-time Dashboard]
```

### Key Components

#### 1. API Layer (`src/api/`)
- **messages.py** - POST /v1/messages (Producer API)
- **conversations.py** - GET /v1/conversations/:id/insights (Consumer API)
- **websocket.py** - WebSocket streaming endpoint
- **health.py** - Health/readiness/liveness checks

#### 2. Kafka Infrastructure (`src/kafka/`)
- **producer.py** - KafkaProducerService with error handling
- **consumer.py** - BaseKafkaConsumer with DLQ pattern
- **admin.py** - Topic management and creation

#### 3. AI Services (`src/ai/`)
- **gemini_service.py** - Google Gemini integration with:
  - Rate limiting (1000 RPM)
  - Structured JSON outputs
  - Async processing
  - Error handling & retries

#### 4. AI Agent Consumers (`src/consumers/`)
- **conversation_processor.py** - Builds conversation state
- **sentiment_agent.py** - Analyzes sentiment & emotion
- **pii_agent.py** - Detects PII in messages
- **insights_agent.py** - Extracts intent, urgency, actions
- **summary_agent.py** - Generates conversation summaries
- **aggregation_consumer.py** - Combines all AI outputs

#### 5. Data Models (`src/models/`)
- **messages.py** - Message schemas (CreateMessageRequest, SupportMessage)
- **intelligence.py** - AI result schemas (Sentiment, PII, Insights, Summary)
- **conversation.py** - Conversation state management

#### 6. Configuration (`src/config/`)
- **settings.py** - Pydantic settings with validation

## 📊 Kafka Topics

| Topic Name | Description | Producer | Consumer |
|------------|-------------|----------|----------|
| `support.messages.raw` | Raw incoming messages | API | Conversation Processor |
| `support.conversations.state` | Conversation context | Conversation Processor | AI Agents |
| `support.ai.sentiment` | Sentiment analysis | Sentiment Agent | Aggregation Consumer |
| `support.ai.pii` | PII detection | PII Agent | Aggregation Consumer |
| `support.ai.insights` | Intent & insights | Insights Agent | Aggregation Consumer |
| `support.ai.summary` | Summaries | Summary Agent | Aggregation Consumer |
| `support.ai.aggregated` | Combined intelligence | Aggregation Consumer | API/WebSocket |
| `support.dlq` | Dead letter queue | Any Consumer | Manual Review |

## 🔄 Data Flow Example

### Step 1: Customer Sends Message

```json
POST /v1/messages
{
  "conversation_id": "conv_123",
  "sender": "customer",
  "message": "I'm very frustrated with my order!",
  "channel": "chat"
}
```

### Step 2: Message → Kafka

```
Topic: support.messages.raw
Key: conv_123
Value: {
  "message_id": "uuid-...",
  "conversation_id": "conv_123",
  "tenant_id": "demo-tenant",
  "sender": "customer",
  "message": "I'm very frustrated with my order!",
  "timestamp": "2025-12-25T10:30:00Z"
}
```

### Step 3: Conversation State Built

```
Topic: support.conversations.state
Key: conv_123
Value: {
  "conversation_id": "conv_123",
  "tenant_id": "demo-tenant",
  "message_count": 1,
  "recent_messages": [...],
  "last_activity": "2025-12-25T10:30:00Z"
}
```

### Step 4: AI Agents Process (Parallel)

**Sentiment Agent:**
```
Topic: support.ai.sentiment
Value: {
  "sentiment": "negative",
  "confidence": 0.89,
  "emotion": "frustrated",
  "reasoning": "Customer expressing dissatisfaction"
}
```

**PII Agent:**
```
Topic: support.ai.pii
Value: {
  "has_pii": false,
  "entities": []
}
```

**Insights Agent:**
```
Topic: support.ai.insights
Value: {
  "intent": "complaint",
  "urgency": "high",
  "suggested_actions": ["Apologize", "Investigate order"],
  "requires_escalation": false
}
```

### Step 5: Aggregation

```
Topic: support.ai.aggregated
Key: conv_123
Value: {
  "conversation_id": "conv_123",
  "sentiment": {...},
  "pii": {...},
  "insights": {...},
  "summary": {...},
  "last_updated": "2025-12-25T10:30:03Z"
}
```

### Step 6: Delivered to Client

**Via Polling:**
```
GET /v1/conversations/conv_123/insights
→ Returns aggregated intelligence
```

**Via WebSocket:**
```
ws://localhost:8000/ws/conversations/conv_123/stream
→ Receives real-time updates:
{
  "type": "intelligence_update",
  "data": { ...aggregated_intelligence... }
}
```

## 🎨 Design Patterns Used

### 1. Event Sourcing
- All events (messages) are immutable and stored in Kafka
- Complete audit trail
- Can replay events to rebuild state

### 2. CQRS (Command Query Responsibility Segregation)
- **Command**: POST /v1/messages (write)
- **Query**: GET /v1/insights (read)
- Separate read and write paths

### 3. Dead Letter Queue (DLQ)
- Failed messages go to `support.dlq` after retries
- Prevents data loss
- Allows manual inspection and retry

### 4. Fan-out Pattern
- One conversation → Multiple AI agents process in parallel
- Reduces latency
- Independent agent scaling

### 5. Aggregation Pattern
- Multiple streams → Single unified view
- Join by conversation_id + tenant_id
- Cache latest state for fast lookups

### 6. Multi-Tenancy
- `tenant_id` in all messages
- Kafka headers for isolation
- Future: per-tenant partitions

### 7. Graceful Shutdown
- Commit Kafka offsets before exit
- Flush pending messages
- Close connections properly

## 🚀 Features

### ✅ Implemented

- [x] Multi-tenant message ingestion API
- [x] Kafka producer with error handling
- [x] Base consumer with DLQ pattern
- [x] Conversation state management
- [x] 4 AI agents (Sentiment, PII, Insights, Summary)
- [x] Aggregation consumer
- [x] RESTful intelligence API
- [x] WebSocket streaming
- [x] Graceful startup/shutdown
- [x] Health checks
- [x] Structured logging
- [x] Rate limiting for Gemini API
- [x] Docker support
- [x] Comprehensive documentation

### 🔮 Future Enhancements

- [ ] Authentication & Authorization (JWT/OAuth2)
- [ ] Persistent state store (Redis/PostgreSQL)
- [ ] Schema Registry (Avro/Protobuf)
- [ ] Monitoring (Prometheus metrics)
- [ ] Distributed tracing (Jaeger/Zipkin)
- [ ] Per-tenant Kafka partitions
- [ ] Conversation routing rules
- [ ] Custom AI agent plugins
- [ ] Webhooks for intelligence updates
- [ ] Historical conversation search
- [ ] Analytics dashboard

## 📁 Project Structure

```
backend/
├── src/
│   ├── api/                    # FastAPI routers
│   │   ├── __init__.py
│   │   ├── messages.py         # POST /v1/messages
│   │   ├── conversations.py    # GET /v1/conversations/:id/insights
│   │   ├── websocket.py        # WebSocket streaming
│   │   └── health.py           # Health checks
│   │
│   ├── ai/                     # AI services
│   │   ├── __init__.py
│   │   └── gemini_service.py   # Gemini API integration
│   │
│   ├── kafka/                  # Kafka infrastructure
│   │   ├── __init__.py
│   │   ├── producer.py         # KafkaProducerService
│   │   ├── consumer.py         # BaseKafkaConsumer
│   │   └── admin.py            # KafkaAdminService
│   │
│   ├── consumers/              # AI agent consumers
│   │   ├── __init__.py
│   │   ├── conversation_processor.py
│   │   ├── sentiment_agent.py
│   │   ├── pii_agent.py
│   │   ├── insights_agent.py
│   │   ├── summary_agent.py
│   │   └── aggregation_consumer.py
│   │
│   ├── models/                 # Pydantic models
│   │   ├── __init__.py
│   │   ├── messages.py         # Message schemas
│   │   ├── intelligence.py     # AI result schemas
│   │   └── conversation.py     # Conversation state
│   │
│   ├── config/                 # Configuration
│   │   ├── __init__.py
│   │   └── settings.py         # Pydantic settings
│   │
│   └── main.py                 # FastAPI application
│
├── requirements.txt            # Python dependencies
├── pyproject.toml              # Poetry configuration
├── Dockerfile                  # Docker image
├── .env.example                # Environment template
├── .gitignore                  # Git ignore rules
│
├── README.md                   # Main documentation
├── SETUP.md                    # Setup guide
├── API_GUIDE.md                # API integration guide
├── PROJECT_OVERVIEW.md         # This file
│
├── run.py                      # Application runner
└── example.py                  # Demo script
```

## 🧪 Testing

### Manual Testing

```bash
# 1. Run the application
python run.py

# 2. Send a test message
curl -X POST "http://localhost:8000/v1/messages" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "test-123",
    "sender": "customer",
    "message": "I need help!",
    "channel": "chat"
  }'

# 3. Wait 5 seconds for processing

# 4. Get intelligence
curl "http://localhost:8000/v1/conversations/test-123/insights"

# 5. Run example script
python example.py
```

### Integration Testing

```bash
# Run tests (when test suite is added)
pytest tests/ -v

# Coverage
pytest --cov=src tests/
```

## 🔧 Configuration

### Environment Variables

See `.env.example` for all configuration options.

**Required:**
- `KAFKA_BOOTSTRAP_SERVERS` - Confluent Cloud bootstrap servers
- `KAFKA_API_KEY` - API key
- `KAFKA_API_SECRET` - API secret

Legacy env vars are still supported (deprecated): `KAFKA_SASL_USERNAME`, `KAFKA_SASL_PASSWORD`.
- `GEMINI_API_KEY` - Google Gemini API key

**Optional:**
- `GEMINI_MODEL` - Model name (default: gemini-1.5-pro)
- `GEMINI_TEMPERATURE` - Creativity (default: 0.3)
- `MAX_CONCURRENT_AI_REQUESTS` - Concurrency limit (default: 50)
- `GEMINI_RPM_LIMIT` - Rate limit (default: 1000)

## 🎓 Key Learnings

1. **Kafka as the backbone**: All data flows through Kafka for reliability
2. **Async Python**: FastAPI + asyncio for high concurrency
3. **Structured outputs**: Gemini's JSON mode ensures parseable results
4. **Error handling**: DLQ pattern prevents data loss
5. **Multi-tenancy**: Design for SaaS from day one
6. **Real-time**: WebSockets for live updates to dashboards
7. **Graceful operations**: Proper startup/shutdown lifecycle

## 📈 Performance Characteristics

- **Message Ingestion**: <10ms (API → Kafka)
- **AI Processing**: 2-5 seconds per agent (Gemini API latency)
- **Total Latency**: 5-10 seconds (message → intelligence)
- **Throughput**: 1000+ messages/minute (limited by Gemini RPM)
- **Scalability**: Horizontal (add more consumer instances)

## 🔐 Security Notes

- **Multi-tenancy**: Enforced via tenant_id
- **PII Detection**: Automatic flagging of sensitive data
- **Kafka ACLs**: Configure in Confluent Cloud
- **API Auth**: Add JWT/OAuth2 for production
- **Network**: Use HTTPS/WSS in production
- **Secrets**: Use secret manager (not .env files)

## 📚 Documentation Files

1. **README.md** - Main documentation with architecture and API reference
2. **SETUP.md** - Step-by-step setup guide for developers
3. **API_GUIDE.md** - Comprehensive API integration guide for customers
4. **PROJECT_OVERVIEW.md** - This file (architecture deep-dive)

## 🎯 Success Criteria

This platform succeeds if:

✅ Any application can integrate with one API endpoint
✅ Intelligence updates in <10 seconds
✅ Agents receive real-time coaching
✅ New AI agents can be added without breaking consumers
✅ System is horizontally scalable
✅ Zero message loss (even on failures)

---

**Built with ❤️ using Confluent Kafka, Google Gemini AI, and FastAPI**
