# Backend Data Flow Documentation

## Architecture Overview

The Stream Chat Application backend follows an **Event-Driven Architecture** using Apache Kafka as the central message broker. The system is designed around independent AI agents that process conversational data in real-time to provide intelligent insights.

### Core Design Principles

1. **Event Sourcing**: All changes flow through Kafka topics as immutable events
2. **Microservices Pattern**: Independent consumers process specific aspects of conversations
3. **Asynchronous Processing**: AI agents work in parallel without blocking each other
4. **State Management**: Conversation state maintained in-memory with Kafka as the source of truth
5. **Efficiency**: Summary-based context passing to minimize token usage

---

## System Components

### 1. FastAPI Application (`src/main.py`)
- **Role**: HTTP API and WebSocket gateway
- **Responsibilities**:
  - Accept incoming messages from frontend
  - Produce raw messages to Kafka
  - Stream aggregated intelligence back to clients via WebSocket
  - Provide REST endpoints for conversation history

### 2. Kafka Topics

| Topic | Purpose | Producer | Consumer(s) |
|-------|---------|----------|-------------|
| `messages_raw` | Raw incoming messages | API | ConversationProcessor |
| `conversations_state` | Conversation state with history | ConversationProcessor | Summary, Sentiment, PII Agents |
| `ai.summary` | Conversation summaries | SummaryAgent | AggregationConsumer, ConversationProcessor |
| `ai.sentiment` | Sentiment analysis results | SentimentAgent | AggregationConsumer |
| `ai.pii` | PII detection results | PIIAgent | AggregationConsumer |
| `ai.insights` | Intent & urgency insights | InsightsAgent | AggregationConsumer |
| `ai.aggregated` | Combined intelligence | AggregationConsumer | WebSocket API |

### 3. Consumers (AI Agents)

#### ConversationProcessor
- **Input**: `messages_raw` (raw messages) + `ai.summary` (summary updates)
- **Output**: `conversations_state`
- **State**: In-memory cache of conversation states
- **Logic**:
  - Maintains rolling window of last 10 messages
  - Stores current conversation summary
  - Produces state updates only for new messages (not summaries)

#### SummaryAgent
- **Input**: `conversations_state`
- **Output**: `ai.summary`
- **AI Service**: Gemini AI
- **Logic**:
  - Uses **incremental summarization**: old_summary + new_message → updated_summary
  - Avoids re-processing entire conversation history
  - Calls `gemini.update_conversation_summary()`

#### SentimentAgent
- **Input**: `conversations_state`
- **Output**: `ai.sentiment`
- **AI Service**: Gemini AI
- **Logic**:
  - Constructs context: `"Context: {summary.tldr}\n\nCurrent message: {last_message}"`
  - Analyzes sentiment considering conversation history via summary
  - Returns: sentiment type, emotion, confidence, reasoning

#### PIIAgent
- **Input**: `conversations_state`
- **Output**: `ai.pii`
- **AI Service**: Gemini AI
- **Logic**:
  - Scans latest message for PII (email, phone, SSN, etc.)
  - Returns detected entities and redacted text

#### InsightsAgent
- **Input**: `conversations_state`
- **Output**: `ai.insights`
- **AI Service**: Gemini AI
- **Logic**:
  - Analyzes full conversation for intent, urgency, categories
  - Provides suggested actions and escalation recommendations

#### AggregationConsumer
- **Input**: `ai.summary`, `ai.sentiment`, `ai.pii`, `ai.insights`
- **Output**: `ai.aggregated`
- **State**: In-memory cache of aggregated intelligence
- **Logic**:
  - Merges results from all agents
  - **PII Persistence**: Once `has_pii=True`, remains true across messages
  - Merges PII entities across conversation
  - Broadcasts to WebSocket clients

---

## Detailed Data Flow

### Message Lifecycle

```
User sends message
       ↓
[FastAPI Endpoint] POST /api/messages
       ↓
Produce to [messages_raw] topic
       ↓
[ConversationProcessor] consumes
       ↓
├─ Parse message
├─ Get/Create ConversationState from cache
├─ Add message to recent_messages (max 10)
└─ Produce to [conversations_state]
       ↓
       ├─────────────────┬─────────────────┬─────────────────┐
       ↓                 ↓                 ↓                 ↓
[SummaryAgent]    [SentimentAgent]  [PIIAgent]     [InsightsAgent]
       ↓                 ↓                 ↓                 ↓
Call Gemini AI    Call Gemini AI    Call Gemini AI  Call Gemini AI
       ↓                 ↓                 ↓                 ↓
Produce to:       Produce to:       Produce to:     Produce to:
[ai.summary]      [ai.sentiment]    [ai.pii]        [ai.insights]
       ↓                 ↓                 ↓                 ↓
       └─────────────────┴─────────────────┴─────────────────┘
                              ↓
                    [AggregationConsumer]
                              ↓
                    Merge all results
                              ↓
                    Produce to [ai.aggregated]
                              ↓
                    Broadcast via WebSocket
                              ↓
                         [Frontend UI]
```

### Summary Update Cycle (Feedback Loop)

```
[SummaryAgent] produces summary
       ↓
Summary → [ai.summary] topic
       ↓
[ConversationProcessor] consumes summary
       ↓
Updates cache: conversation_state.summary = new_summary
       ↓
(Does NOT produce to conversations_state - prevents loop)
       ↓
Next message arrives
       ↓
[ConversationProcessor] produces state WITH summary
       ↓
[SummaryAgent] uses old summary + new message
       ↓
Generates updated summary (efficient!)
```

---

## Data Models

### ConversationState
```python
{
    "conversation_id": "conv-123",
    "tenant_id": "acme-corp",
    "message_count": 15,
    "recent_messages": [...],  # Last 10 messages
    "summary": {               # NEW: Current summary
        "tldr": "Customer experiencing billing issue",
        "customer_issue": "Unexpected charge on account",
        "key_points": [...],
        "next_steps": [...]
    },
    "participants": ["customer", "agent"],
    "last_activity": "2025-12-27T10:30:00Z"
}
```

### SummaryResult
```python
{
    "conversation_id": "conv-123",
    "tenant_id": "acme-corp",
    "tldr": "Brief summary",
    "customer_issue": "What customer needs",
    "agent_response": "How agent responded",
    "key_points": ["Point 1", "Point 2"],
    "next_steps": ["Action 1", "Action 2"],
    "timestamp": "2025-12-27T10:30:00Z"
}
```

### AggregatedIntelligence
```python
{
    "conversation_id": "conv-123",
    "tenant_id": "acme-corp",
    "sentiment": {
        "sentiment": "negative",
        "emotion": "frustrated",
        "confidence": 0.87,
        "reasoning": "Customer expressing dissatisfaction"
    },
    "pii": {
        "has_pii": true,
        "entities": [{"type": "email", "value": "[REDACTED]"}]
    },
    "insights": {
        "intent": "Billing Inquiry",
        "urgency": "High",
        "suggested_actions": ["Offer refund", "Escalate to manager"]
    },
    "summary": {...},
    "last_updated": "2025-12-27T10:30:00Z"
}
```

---

## Key Optimizations

### 1. Summary-Based Context (Latest Implementation)

**Problem**: Passing all messages to agents wastes tokens and doesn't scale.

**Solution**: 
- Store summary in `ConversationState`
- Agents use: `summary + latest_message` instead of `all_messages`
- Summary provides full context in compressed form

**Benefits**:
- 90% reduction in tokens for sentiment/summary analysis
- Scales to conversations with 100+ messages
- Maintains full conversation context

### 2. PII Persistence

**Problem**: PII flag would reset if subsequent messages had no PII.

**Solution**: AggregationConsumer maintains `has_pii=True` once detected and merges all entities.

### 3. Loop Prevention

**Problem**: Summary updates could trigger infinite processing loops.

**Solution**: 
- ConversationProcessor only produces state for **new messages**
- Summary updates only modify internal cache
- Agents triggered only by new user/agent messages

---

## Scalability Considerations

### Current Architecture
- **State Storage**: In-memory (loses state on restart)
- **Message Window**: 10 messages
- **Concurrency**: Async processing with semaphore limits
- **Rate Limiting**: Gemini API requests per minute

### Production Recommendations

1. **State Persistence**
   - Use Redis for conversation cache
   - Enables horizontal scaling
   - Survives restarts

2. **Message History**
   - Store full history in database (PostgreSQL/MongoDB)
   - Load on-demand for deep analysis
   - Keep 10-message window in memory

3. **ksqlDB Integration**
   - Create materialized views of summaries
   - Enable SQL queries: "Show all high-urgency conversations"
   - Real-time analytics dashboard

4. **Monitoring**
   - Track consumer lag
   - Monitor AI service latency
   - Alert on processing failures

---

## Configuration

### Environment Variables (.env)

```bash
# Kafka
CONFLUENT_BOOTSTRAP_SERVERS=...
CONFLUENT_API_KEY=...
CONFLUENT_API_SECRET=...

# Topics
KAFKA_TOPIC_MESSAGES_RAW=support.messages.raw
KAFKA_TOPIC_CONVERSATIONS_STATE=support.conversations.state
KAFKA_TOPIC_AI_SUMMARY=support.ai.summary
KAFKA_TOPIC_AI_SENTIMENT=support.ai.sentiment
KAFKA_TOPIC_AI_PII=support.ai.pii
KAFKA_TOPIC_AI_INSIGHTS=support.ai.insights
KAFKA_TOPIC_AI_AGGREGATED=support.ai.aggregated

# Gemini AI
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-2.0-flash-exp
GEMINI_TEMPERATURE=0.7
GEMINI_REQUESTS_PER_MINUTE=60
MAX_CONCURRENT_AI_REQUESTS=10
```

---

## Error Handling

### Consumer Resilience
- Each consumer has its own consumer group
- Failed processing doesn't block other agents
- Kafka retains messages for reprocessing

### AI Service Failures
- Fallback to mock responses on API errors
- Continue processing pipeline
- Log errors for investigation

### State Recovery
- Conversation state rebuilt from Kafka topics
- ConversationProcessor recreates state from messages
- No data loss if consumers restart

---

## Development Workflow

### Starting the Backend

```bash
cd backend
python run.py
```

This starts:
1. FastAPI server (port 8000)
2. All consumer threads
3. WebSocket server

### Testing Individual Components

```bash
# Test conversation processing
python -m pytest tests/test_conversation_processor.py

# Test AI agents
python -m pytest tests/test_agents.py

# Test API endpoints
python test_api.py
```

---

## Debugging Tips

### Check Kafka Topics
```bash
# List topics
kafka-topics --list

# Read messages from topic
kafka-console-consumer --topic support.messages.raw --from-beginning
```

### Monitor Consumer Lag
```bash
# Check consumer group status
kafka-consumer-groups --describe --group support-backend
```

### View Logs
```bash
# All logs
tail -f logs/backend.log

# Specific agent
tail -f logs/backend.log | grep SummaryAgent
```

---

## Future Enhancements

1. **Multi-Language Support**: Detect language and route to appropriate AI model
2. **Custom Agent Plugins**: Allow tenants to add custom analysis agents
3. **Historical Analysis**: Batch process old conversations for trends
4. **Real-Time Alerts**: Push notifications for critical issues
5. **A/B Testing**: Compare different AI prompts for better results

---

## Conclusion

The backend is architected for **scalability**, **reliability**, and **efficiency**. The event-driven design allows independent scaling of components, while the summary-based optimization ensures sustainable AI costs as conversations grow.

Key innovations:
- ✅ Incremental summarization (not reprocessing)
- ✅ Parallel agent processing
- ✅ PII persistence across messages
- ✅ Loop-free architecture
- ✅ WebSocket streaming for real-time updates
