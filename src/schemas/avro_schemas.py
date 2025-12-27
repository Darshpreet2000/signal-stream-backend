"""Avro schemas for all Kafka message types."""

# Message Schema - for support.messages.raw topic
MESSAGE_SCHEMA = {
    "type": "record",
    "name": "SupportMessage",
    "namespace": "com.signalstream.support",
    "fields": [
        {"name": "message_id", "type": "string"},
        {"name": "conversation_id", "type": "string"},
        {"name": "tenant_id", "type": "string"},
        {"name": "sender_role", "type": {"type": "enum", "name": "SenderRole", "symbols": ["customer", "agent"]}},
        {"name": "content", "type": "string"},
        {"name": "timestamp", "type": "string"},
        {"name": "metadata", "type": ["null", {"type": "map", "values": "string"}], "default": None}
    ]
}

# Conversation State Schema - for support.conversations.state topic
CONVERSATION_STATE_SCHEMA = {
    "type": "record",
    "name": "ConversationState",
    "namespace": "com.signalstream.support",
    "fields": [
        {"name": "conversation_id", "type": "string"},
        {"name": "tenant_id", "type": "string"},
        {"name": "status", "type": {"type": "enum", "name": "ConversationStatus", "symbols": ["active", "resolved", "escalated"]}},
        {"name": "message_count", "type": "int"},
        {"name": "last_message_timestamp", "type": "string"},
        {"name": "messages", "type": {"type": "array", "items": "string"}},  # Array of message contents
        {"name": "created_at", "type": "string"},
        {"name": "updated_at", "type": "string"}
    ]
}

# Sentiment Analysis Schema - for support.ai.sentiment topic
SENTIMENT_SCHEMA = {
    "type": "record",
    "name": "SentimentAnalysis",
    "namespace": "com.signalstream.ai",
    "fields": [
        {"name": "conversation_id", "type": "string"},
        {"name": "message_id", "type": "string"},
        {"name": "sentiment", "type": {"type": "enum", "name": "Sentiment", "symbols": ["positive", "neutral", "negative"]}},
        {"name": "emotion", "type": "string"},
        {"name": "confidence", "type": "double"},
        {"name": "reasoning", "type": ["null", "string"], "default": None},
        {"name": "timestamp", "type": "string"}
    ]
}

# PII Detection Schema - for support.ai.pii topic
PII_SCHEMA = {
    "type": "record",
    "name": "PIIDetection",
    "namespace": "com.signalstream.ai",
    "fields": [
        {"name": "conversation_id", "type": "string"},
        {"name": "message_id", "type": "string"},
        {"name": "has_pii", "type": "boolean"},
        {"name": "entities", "type": {
            "type": "array",
            "items": {
                "type": "record",
                "name": "PIIEntity",
                "fields": [
                    {"name": "type", "type": "string"},
                    {"name": "value", "type": "string"},
                    {"name": "confidence", "type": "double"}
                ]
            }
        }},
        {"name": "risk_level", "type": ["null", "string"], "default": None},
        {"name": "timestamp", "type": "string"}
    ]
}

# Insights Schema - for support.ai.insights topic
INSIGHTS_SCHEMA = {
    "type": "record",
    "name": "CustomerInsights",
    "namespace": "com.signalstream.ai",
    "fields": [
        {"name": "conversation_id", "type": "string"},
        {"name": "message_id", "type": "string"},
        {"name": "intent", "type": "string"},
        {"name": "urgency", "type": "string"},
        {"name": "suggested_actions", "type": {"type": "array", "items": "string"}},
        {"name": "requires_escalation", "type": "boolean"},
        {"name": "reasoning", "type": ["null", "string"], "default": None},
        {"name": "timestamp", "type": "string"}
    ]
}

# Summary Schema - for support.ai.summary topic
SUMMARY_SCHEMA = {
    "type": "record",
    "name": "ConversationSummary",
    "namespace": "com.signalstream.ai",
    "fields": [
        {"name": "conversation_id", "type": "string"},
        {"name": "tldr", "type": "string"},
        {"name": "key_points", "type": {"type": "array", "items": "string"}},
        {"name": "resolution_status", "type": ["null", "string"], "default": None},
        {"name": "timestamp", "type": "string"}
    ]
}

# Aggregated Intelligence Schema - for support.ai.aggregated topic
AGGREGATED_INTELLIGENCE_SCHEMA = {
    "type": "record",
    "name": "AggregatedIntelligence",
    "namespace": "com.signalstream.ai",
    "fields": [
        {"name": "conversation_id", "type": "string"},
        {"name": "sentiment", "type": ["null", {
            "type": "record",
            "name": "SentimentData",
            "fields": [
                {"name": "sentiment", "type": "string"},
                {"name": "emotion", "type": "string"},
                {"name": "confidence", "type": "double"},
                {"name": "reasoning", "type": ["null", "string"], "default": None}
            ]
        }], "default": None},
        {"name": "pii", "type": ["null", {
            "type": "record",
            "name": "PIIData",
            "fields": [
                {"name": "has_pii", "type": "boolean"},
                {"name": "entities", "type": {"type": "array", "items": {
                    "type": "record",
                    "name": "PIIEntityData",
                    "fields": [
                        {"name": "type", "type": "string"},
                        {"name": "value", "type": "string"},
                        {"name": "confidence", "type": "double"}
                    ]
                }}},
                {"name": "risk_level", "type": ["null", "string"], "default": None}
            ]
        }], "default": None},
        {"name": "insights", "type": ["null", {
            "type": "record",
            "name": "InsightsData",
            "fields": [
                {"name": "intent", "type": "string"},
                {"name": "urgency", "type": "string"},
                {"name": "suggested_actions", "type": {"type": "array", "items": "string"}},
                {"name": "requires_escalation", "type": "boolean"},
                {"name": "reasoning", "type": ["null", "string"], "default": None}
            ]
        }], "default": None},
        {"name": "summary", "type": ["null", {
            "type": "record",
            "name": "SummaryData",
            "fields": [
                {"name": "tldr", "type": "string"},
                {"name": "key_points", "type": {"type": "array", "items": "string"}},
                {"name": "resolution_status", "type": ["null", "string"], "default": None}
            ]
        }], "default": None},
        {"name": "timestamp", "type": "string"}
    ]
}
