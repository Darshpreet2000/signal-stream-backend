# SignalStream AI - API Integration Guide

Complete guide for customer applications integrating with SignalStream AI.

## Base URL

```
Production: https://api.signalstream.ai
Development: http://localhost:8000
```

## Authentication

**Current Version**: No authentication required for demo
**Production**: Contact us for API keys and tenant credentials

## Core Concepts

### Multi-Tenancy

All data is isolated by `tenant_id`. In production, your tenant ID will be provided during onboarding.

### Conversation Flow

1. **Send Messages** → Messages are ingested and queued
2. **AI Processing** → Multiple AI agents analyze in parallel
3. **Receive Intelligence** → Get results via polling or streaming

### Message Types

- `customer` - Messages from your customers
- `agent` - Messages from your support agents
- `system` - Automated system messages

## API Reference

### 1. Ingest Message

**Endpoint**: `POST /v1/messages`

Submit a support message for AI analysis.

#### Request

```json
{
  "conversation_id": "string",       // Required: Unique conversation ID
  "sender": "customer | agent",      // Required: Who sent the message
  "message": "string",               // Required: Message content (max 10,000 chars)
  "channel": "chat | email | voice | sms",  // Optional: Default "chat"
  "tenant_id": "string",             // Optional: Your tenant ID
  "metadata": {                      // Optional: Custom metadata
    "user_id": "usr_123",
    "session_id": "sess_456"
  }
}
```

#### Response (202 Accepted)

```json
{
  "message_id": "uuid",
  "conversation_id": "string",
  "status": "accepted",
  "timestamp": "2025-12-25T10:30:00Z"
}
```

#### Example (Python)

```python
import requests

response = requests.post(
    "http://localhost:8000/v1/messages",
    json={
        "conversation_id": "conv_12345",
        "sender": "customer",
        "message": "I'm having trouble with my order",
        "channel": "chat"
    }
)

print(response.json())
# {'message_id': '550e8400-...', 'status': 'accepted', ...}
```

#### Example (JavaScript)

```javascript
fetch('http://localhost:8000/v1/messages', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    conversation_id: 'conv_12345',
    sender: 'customer',
    message: "I'm having trouble with my order",
    channel: 'chat'
  })
})
.then(res => res.json())
.then(data => console.log(data));
```

#### Example (cURL)

```bash
curl -X POST "http://localhost:8000/v1/messages" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "conv_12345",
    "sender": "customer",
    "message": "I need help with my order",
    "channel": "chat"
  }'
```

---

### 2. Get Conversation Intelligence

**Endpoint**: `GET /v1/conversations/{conversation_id}/insights`

Retrieve AI-generated intelligence for a conversation.

#### Query Parameters

- `tenant_id` (optional): Your tenant ID

#### Response (200 OK)

```json
{
  "conversation_id": "conv_12345",
  "tenant_id": "your-tenant",
  "sentiment": {
    "sentiment": "negative | neutral | positive",
    "confidence": 0.87,
    "emotion": "angry | frustrated | satisfied | confused | urgent | happy | neutral",
    "reasoning": "Customer expressing dissatisfaction with service",
    "timestamp": "2025-12-25T10:30:00Z"
  },
  "pii": {
    "has_pii": true,
    "entities": [
      {
        "type": "email | phone | credit_card | ssn | address | account_number | name",
        "value": "[REDACTED]",
        "start_index": 10,
        "end_index": 30
      }
    ],
    "redacted_text": "Contact me at [REDACTED]",
    "timestamp": "2025-12-25T10:30:01Z"
  },
  "insights": {
    "intent": "refund_request | technical_issue | billing_inquiry | feature_request | complaint | general_inquiry | account_issue | cancellation",
    "urgency": "low | medium | high | critical",
    "categories": ["billing", "refund"],
    "suggested_actions": [
      "Apologize for the inconvenience",
      "Process refund immediately"
    ],
    "requires_escalation": false,
    "estimated_resolution_time": "< 1 hour | 1-4 hours | 4-24 hours | 1-3 days",
    "key_concerns": [
      "Duplicate charge",
      "Wants immediate refund"
    ],
    "timestamp": "2025-12-25T10:30:02Z"
  },
  "summary": {
    "tldr": "Customer requesting refund for duplicate charge",
    "customer_issue": "Charged twice for the same order",
    "agent_actions": [
      "Verified duplicate charge",
      "Initiated refund process"
    ],
    "resolution": "Refund processed, customer satisfied",
    "follow_up_needed": false,
    "timestamp": "2025-12-25T10:30:03Z"
  },
  "last_updated": "2025-12-25T10:30:03Z"
}
```

#### Response (404 Not Found)

```json
{
  "detail": "Conversation 'conv_12345' not found or not yet processed"
}
```

#### Example (Python)

```python
import requests
import time

# Send message
requests.post("http://localhost:8000/v1/messages", json={...})

# Wait for processing (in production, use webhooks or WebSocket)
time.sleep(5)

# Get intelligence
response = requests.get(
    "http://localhost:8000/v1/conversations/conv_12345/insights"
)

intelligence = response.json()
print(f"Sentiment: {intelligence['sentiment']['sentiment']}")
print(f"Intent: {intelligence['insights']['intent']}")
print(f"Urgency: {intelligence['insights']['urgency']}")
```

---

### 3. Stream Real-time Intelligence

**Endpoint**: `WebSocket ws://localhost:8000/ws/conversations/{conversation_id}/stream`

Subscribe to real-time intelligence updates as AI agents process the conversation.

#### Connection Message

```json
{
  "type": "connected",
  "conversation_id": "conv_12345",
  "message": "Connected to conversation stream"
}
```

#### Intelligence Update Message

```json
{
  "type": "intelligence_update",
  "conversation_id": "conv_12345",
  "data": {
    // Full AggregatedIntelligence object (see above)
  }
}
```

#### Pong Message (Response to ping)

```json
{
  "type": "pong"
}
```

#### Example (Python)

```python
import asyncio
import websockets
import json

async def stream_intelligence(conversation_id):
    uri = f"ws://localhost:8000/ws/conversations/{conversation_id}/stream"
    
    async with websockets.connect(uri) as websocket:
        # Receive connection message
        message = await websocket.recv()
        print(f"Connected: {message}")
        
        # Listen for updates
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            
            if data["type"] == "intelligence_update":
                print(f"New intelligence:")
                print(f"  Sentiment: {data['data']['sentiment']['sentiment']}")
                print(f"  Intent: {data['data']['insights']['intent']}")
            
            # Send ping to keep alive
            await websocket.send("ping")

# Run
asyncio.run(stream_intelligence("conv_12345"))
```

#### Example (JavaScript)

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/conversations/conv_12345/stream');

ws.onopen = () => {
  console.log('Connected to intelligence stream');
  
  // Send ping every 30 seconds
  setInterval(() => ws.send('ping'), 30000);
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'intelligence_update') {
    console.log('Intelligence update:', data.data);
    
    // Update your UI
    updateSentimentDisplay(data.data.sentiment);
    updateInsightsDisplay(data.data.insights);
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Disconnected from intelligence stream');
};
```

---

## Health & Monitoring

### Health Check

**Endpoint**: `GET /health`

```json
{
  "status": "healthy | degraded",
  "kafka_connected": true,
  "version": "0.1.0"
}
```

### Readiness Check

**Endpoint**: `GET /ready`

```json
{
  "ready": true
}
```

### Liveness Check

**Endpoint**: `GET /live`

```json
{
  "alive": true
}
```

---

## Integration Patterns

### Pattern 1: Fire and Forget

Send messages without waiting for intelligence.

```python
def send_support_message(conversation_id, message):
    requests.post("http://localhost:8000/v1/messages", json={
        "conversation_id": conversation_id,
        "sender": "customer",
        "message": message
    })
    # Intelligence will be available later via polling or webhooks
```

### Pattern 2: Polling

Send message, wait, then poll for intelligence.

```python
def get_message_intelligence(conversation_id, message):
    # Send message
    requests.post("http://localhost:8000/v1/messages", json={
        "conversation_id": conversation_id,
        "sender": "customer",
        "message": message
    })
    
    # Wait for processing
    time.sleep(5)
    
    # Get intelligence
    response = requests.get(
        f"http://localhost:8000/v1/conversations/{conversation_id}/insights"
    )
    return response.json()
```

### Pattern 3: WebSocket Streaming (Recommended)

Real-time intelligence as it becomes available.

```python
async def live_intelligence_dashboard(conversation_id):
    uri = f"ws://localhost:8000/ws/conversations/{conversation_id}/stream"
    
    async with websockets.connect(uri) as websocket:
        async for message in websocket:
            data = json.loads(message)
            if data["type"] == "intelligence_update":
                update_dashboard(data["data"])
```

---

## Use Cases

### Use Case 1: Agent Dashboard

Display real-time intelligence to support agents.

```python
# When conversation starts
conversation_id = create_conversation()

# Connect WebSocket for real-time updates
ws = connect_to_stream(conversation_id)

# As messages come in
for message in incoming_messages:
    send_message(conversation_id, message)
    # Dashboard auto-updates via WebSocket

# Show agent:
# - Current sentiment
# - Detected PII warnings
# - Suggested responses
# - Escalation recommendations
```

### Use Case 2: Auto-routing

Route conversations based on AI insights.

```python
def route_conversation(conversation_id):
    intelligence = get_intelligence(conversation_id)
    
    if intelligence["insights"]["urgency"] == "critical":
        assign_to_senior_agent(conversation_id)
    elif intelligence["insights"]["requires_escalation"]:
        escalate_to_supervisor(conversation_id)
    elif intelligence["pii"]["has_pii"]:
        flag_for_compliance_review(conversation_id)
    else:
        assign_to_available_agent(conversation_id)
```

### Use Case 3: Quality Assurance

Analyze conversations for quality metrics.

```python
def analyze_agent_performance(agent_id, date_range):
    conversations = get_agent_conversations(agent_id, date_range)
    
    metrics = {
        "total_conversations": len(conversations),
        "avg_resolution_time": 0,
        "customer_satisfaction": 0,
        "escalation_rate": 0
    }
    
    for conv in conversations:
        intelligence = get_intelligence(conv["id"])
        
        if intelligence["sentiment"]["sentiment"] == "positive":
            metrics["customer_satisfaction"] += 1
        
        if intelligence["insights"]["requires_escalation"]:
            metrics["escalation_rate"] += 1
    
    return metrics
```

---

## Error Handling

### Common Errors

#### 404 - Conversation Not Found

```json
{
  "detail": "Conversation 'conv_xyz' not found or not yet processed"
}
```

**Cause**: Intelligence not yet available (still processing)
**Solution**: Wait a few seconds and retry, or use WebSocket for real-time updates

#### 500 - Internal Server Error

```json
{
  "detail": "Internal server error"
}
```

**Cause**: Server-side error (Kafka connection, Gemini API, etc.)
**Solution**: Check server logs, verify configuration

#### 422 - Validation Error

```json
{
  "detail": [
    {
      "loc": ["body", "message"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Cause**: Invalid request payload
**Solution**: Check required fields and data types

### Retry Logic

```python
import time
from requests.exceptions import RequestException

def send_message_with_retry(conversation_id, message, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.post(
                "http://localhost:8000/v1/messages",
                json={
                    "conversation_id": conversation_id,
                    "sender": "customer",
                    "message": message
                },
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        
        except RequestException as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff
```

---

## Rate Limits

- **Message Ingestion**: No limit (messages are queued)
- **Intelligence Retrieval**: 100 requests/minute per tenant
- **WebSocket Connections**: 10 concurrent connections per conversation

Contact us for higher limits.

---

## Support

- **Documentation**: https://docs.signalstream.ai
- **Status Page**: https://status.signalstream.ai
- **Support Email**: support@signalstream.ai
- **Developer Slack**: signalstream.slack.com

---

## Changelog

### v0.1.0 (2025-12-25)

- Initial release
- Message ingestion API
- AI agents (sentiment, PII, insights, summary)
- WebSocket streaming
- Multi-tenant support
