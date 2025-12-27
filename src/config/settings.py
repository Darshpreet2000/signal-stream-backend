"""Application settings and configuration using Pydantic."""






































































































































































        }            "last_updated": now            },                "timestamp": now                "next_steps": next_steps,                "key_points": key_points,                "agent_response": agent_response,                "customer_issue": customer_issue,                "tldr": tldr,                "tenant_id": tenant_id,                "conversation_id": conversation_id,            "summary": {            },                "timestamp": now                "key_concerns": ["Locked out of account", "Inability to pay bills" if urgency == "Critical" else "Inability to pay bills on time"],                "estimated_resolution_time": "< 1 hour",                "requires_escalation": requires_escalation,                ] + (["Escalate to senior support"] if requires_escalation else []),                    "Provide immediate resolution"                    "Apologize and acknowledge frustration",                "suggested_actions": [                "categories": ["Account Access", "Financial" if urgency == "Critical" else "Technical Support"],                "urgency": urgency,                "intent": "Account Issue",                "tenant_id": tenant_id,                "conversation_id": conversation_id,            "insights": {            },                "timestamp": now                "redacted_text": redacted_text,                "entities": pii_entities,                "has_pii": self.has_pii,                "tenant_id": tenant_id,                "conversation_id": conversation_id,            "pii": {            },                "timestamp": now                "reasoning": reasoning,                "emotion": emotion_type,                "confidence": confidence,                "sentiment": sentiment_type,                "tenant_id": tenant_id,                "conversation_id": conversation_id,            "sentiment": {            "tenant_id": tenant_id,            "conversation_id": conversation_id,        return {                now = datetime.utcnow().isoformat()                    urgency = "Critical"            requires_escalation = True            ]                "Agent to investigate the cause of the account lockout."                "Agent to verify customer's identity.",            next_steps = [                key_points.append("Customer provided account details and contact information.")            if self.message_count > 2:            ]                "Customer has bills due today."                "Customer is frustrated and needs immediate assistance.",            key_points = [            agent_response = "Agent expresses empathy and commits to resolving the issue quickly." if self.message_count > 1 else None            customer_issue = "Customer is locked out of their bank account and cannot access funds to pay bills due today."            tldr = "Customer is locked out of their bank account and needs immediate access to funds to pay bills."            issue_resolved = False        else:            urgency = "Critical"            requires_escalation = False            next_steps = ["Customer to confirm account access.", "Monitor account activity."]            ]                "Customer can now access their account."                "Customer's account lockout resolved.",            key_points = [            agent_response = "Account restriction removed, online access reset, and bill-pay grace period extended."            customer_issue = "Customer was locked out of their bank account."            tldr = "Customer's account lockout resolved; access restored, bill-pay grace period extended."            issue_resolved = False        elif self.message_count > 3:            urgency = "High"            requires_escalation = False            next_steps = ["Monitor account activity.", "Close the support ticket."]            ]                "Customer confirmed account access."                "Customer can now access their account.",                "Customer's account lockout resolved.",            key_points = [            agent_response = "Account access restored."            customer_issue = "Customer was locked out of their bank account."            tldr = "Customer account access restored; issue resolved; customer confirmed access."            issue_resolved = True        if self.message_count > 5 and sender == "agent":        # Determine issue resolution status                    redacted_text = message_text            pii_entities = []        else:            redacted_text = message_text.replace("Sarah Lee", "[REDACTED]").replace("4421", "[REDACTED]").replace("24456455", "[REDACTED]")            ]                {"type": "phone", "value": "24456455", "start_index": 58, "end_index": 66}                {"type": "account_number", "value": "4421", "start_index": 35, "end_index": 39},                {"type": "name", "value": "Sarah Lee", "start_index": 10, "end_index": 19},            pii_entities = [        if self.has_pii:        # Build PII data                    reasoning = "The customer is providing information or responding neutrally."            confidence = 0.8            emotion_type = "neutral"            sentiment_type = "neutral"        else:            reasoning = "The customer expresses frustration and urgency. The language used indicates a negative emotional state."            confidence = 0.95            emotion_type = "frustrated"            sentiment_type = "negative"        elif any(word in message_text.lower() for word in ["frustrat", "locked", "urgent", "need this fixed"]):            reasoning = "The customer expresses relief and thanks, indicating satisfaction after the issue was resolved."            confidence = 0.95            emotion_type = "satisfied"            sentiment_type = "positive"        if any(word in message_text.lower() for word in ["relief", "thanks", "thank", "great", "perfect", "solved"]):        # Determine sentiment based on message content                    self.has_pii = True        if "name is" in message_text.lower() or any(char.isdigit() for char in message_text):        # Detect PII in message                self.message_count += 1        """            Mock intelligence data        Returns:                        sender: Message sender (customer/agent)            message_text: The message text            tenant_id: Tenant ID            conversation_id: Conversation ID        Args:                """Get mock intelligence data based on message progression.    ) -> Dict[str, Any]:        self, conversation_id: str, tenant_id: str, message_text: str, sender: str    def get_mock_intelligence(        self.has_pii = False        self.message_count = 0        """Initialize mock data scenarios."""    def __init__(self):    """Service that provides mock intelligence data for testing."""class MockIntelligenceService:)    EmotionType,    SentimentType,    IntelligenceData,    SummaryResult,    InsightsResult,    PIIResult,    SentimentResult,from ..models import (from typing import Dict, Anyfrom datetime import datetimefrom functools import lru_cache
from pathlib import Path
from typing import List, Union, Any, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_cors(v: Any) -> List[str]:
    """Parse CORS origins from various formats."""
    if isinstance(v, str):
        return [origin.strip() for origin in v.split(",") if origin.strip()]
    if isinstance(v, list):
        return v
    return [str(v)]


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[2] / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_parse_none_str="null",
    )

    # Application
    app_env: str = Field(default="development", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    api_version: str = Field(default="v1", alias="API_VERSION")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    
    # Mock Mode for Testing
    enable_mock_mode: bool = Field(default=True, alias="ENABLE_MOCK_MODE")

    # Kafka Configuration
    kafka_enabled: bool = Field(default=True, alias="KAFKA_ENABLED")
    kafka_bootstrap_servers: str = Field(default="", alias="KAFKA_BOOTSTRAP_SERVERS")
    # Preferred Confluent Cloud naming
    kafka_api_key: str = Field(default="", alias="KAFKA_API_KEY")
    kafka_api_secret: str = Field(default="", alias="KAFKA_API_SECRET")
    # Backward-compatible naming (deprecated)
    kafka_sasl_username: str = Field(default="", alias="KAFKA_SASL_USERNAME")
    kafka_sasl_password: str = Field(default="", alias="KAFKA_SASL_PASSWORD")
    kafka_sasl_mechanism: str = Field(default="PLAIN", alias="KAFKA_SASL_MECHANISM")
    kafka_security_protocol: str = Field(default="SASL_SSL", alias="KAFKA_SECURITY_PROTOCOL")
    kafka_consumer_group_id: str = Field(
        default="supportpulse-backend", alias="KAFKA_CONSUMER_GROUP_ID"
    )

    # Kafka Topics
    kafka_topic_messages_raw: str = Field(
        default="support.messages.raw", alias="KAFKA_TOPIC_MESSAGES_RAW"
    )
    kafka_topic_conversations_state: str = Field(
        default="support.conversations.state", alias="KAFKA_TOPIC_CONVERSATIONS_STATE"
    )
    kafka_topic_ai_sentiment: str = Field(
        default="support.ai.sentiment", alias="KAFKA_TOPIC_AI_SENTIMENT"
    )
    kafka_topic_ai_pii: str = Field(default="support.ai.pii", alias="KAFKA_TOPIC_AI_PII")
    kafka_topic_ai_insights: str = Field(
        default="support.ai.insights", alias="KAFKA_TOPIC_AI_INSIGHTS"
    )
    kafka_topic_ai_summary: str = Field(
        default="support.ai.summary", alias="KAFKA_TOPIC_AI_SUMMARY"
    )
    kafka_topic_ai_aggregated: str = Field(
        default="support.ai.aggregated", alias="KAFKA_TOPIC_AI_AGGREGATED"
    )
    kafka_topic_dlq: str = Field(default="support.dlq", alias="KAFKA_TOPIC_DLQ")

    # Confluent Schema Registry (optional)
    kafka_schema_registry_url: str = Field(default="", alias="KAFKA_SCHEMA_REGISTRY_URL")
    kafka_schema_registry_api_key: str = Field(default="", alias="KAFKA_SCHEMA_REGISTRY_API_KEY")
    kafka_schema_registry_api_secret: str = Field(default="", alias="KAFKA_SCHEMA_REGISTRY_API_SECRET")

    # ksqlDB (optional)
    ksqldb_url: str = Field(default="", alias="KSQLDB_URL")
    ksqldb_api_key: str = Field(default="", alias="KSQLDB_API_KEY")
    ksqldb_api_secret: str = Field(default="", alias="KSQLDB_API_SECRET")

    # Gemini AI Configuration
    gemini_api_key: str = Field(..., alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-1.5-pro", alias="GEMINI_MODEL")
    gemini_temperature: float = Field(default=0.3, alias="GEMINI_TEMPERATURE")
    gemini_max_output_tokens: int = Field(default=2048, alias="GEMINI_MAX_OUTPUT_TOKENS")
    gemini_rpm_limit: int = Field(default=1000, alias="GEMINI_RPM_LIMIT")

    # Multi-Tenancy
    default_tenant_id: str = Field(default="demo-tenant", alias="DEFAULT_TENANT_ID")
    enable_tenant_isolation: bool = Field(default=True, alias="ENABLE_TENANT_ISOLATION")

    # Rate Limiting
    max_concurrent_ai_requests: int = Field(
        default=50, alias="MAX_CONCURRENT_AI_REQUESTS"
    )
    gemini_requests_per_minute: int = Field(
        default=1000, alias="GEMINI_REQUESTS_PER_MINUTE"
    )

    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001"],
        alias="CORS_ORIGINS",
        json_schema_extra={"env_parse": parse_cors}
    )
    cors_allow_credentials: bool = Field(default=True, alias="CORS_ALLOW_CREDENTIALS")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> List[str]:
        """Parse CORS origins from comma-separated string or list."""
        return parse_cors(v)

    # WebSocket
    ws_heartbeat_interval: int = Field(default=30, alias="WS_HEARTBEAT_INTERVAL")
    ws_message_queue_size: int = Field(default=100, alias="WS_MESSAGE_QUEUE_SIZE")

    # Monitoring
    enable_metrics: bool = Field(default=True, alias="ENABLE_METRICS")
    metrics_port: int = Field(default=9090, alias="METRICS_PORT")

    @property
    def kafka_api_key_effective(self) -> str:
        """Effective Kafka API key.

        Prefer KAFKA_API_KEY; fall back to legacy KAFKA_SASL_USERNAME.
        """
        return self.kafka_api_key or self.kafka_sasl_username

    @property
    def kafka_api_secret_effective(self) -> str:
        """Effective Kafka API secret.

        Prefer KAFKA_API_SECRET; fall back to legacy KAFKA_SASL_PASSWORD.
        """
        return self.kafka_api_secret or self.kafka_sasl_password

    @property
    def kafka_is_configured(self) -> bool:
        """Return True if Kafka is enabled and has enough configuration to connect.

        This allows running the backend in development/demo mode without Confluent Cloud
        credentials (Kafka disabled), while keeping production behavior intact.
        """
        if not self.kafka_enabled:
            return False

        if not self.kafka_bootstrap_servers:
            return False

        protocol = (self.kafka_security_protocol or "").upper()
        if protocol == "PLAINTEXT":
            return True

        # SASL_SSL / SASL_PLAINTEXT
        return bool(self.kafka_api_key_effective and self.kafka_api_secret_effective)

    @property
    def kafka_config(self) -> dict:
        """Get Kafka client configuration.
        
        Matches the style from ccloud-python-client/client.properties for compatibility.
        """
        config = {
            "bootstrap.servers": self.kafka_bootstrap_servers,
            "security.protocol": self.kafka_security_protocol,
        }

        protocol = (self.kafka_security_protocol or "").upper()
        if protocol != "PLAINTEXT":
            config.update(
                {
                    "sasl.mechanism": self.kafka_sasl_mechanism,  # Fixed: singular not plural
                    "sasl.username": self.kafka_api_key_effective,
                    "sasl.password": self.kafka_api_secret_effective,
                    # Fix for macOS SSL certificate issue
                    "ssl.ca.location": "/etc/ssl/cert.pem",
                }
            )

        return config

    @property
    def kafka_producer_config(self) -> dict:
        """Get Kafka producer-specific configuration."""
        config = self.kafka_config.copy()
        config.update(
            {
                "acks": "all",
                "retries": 3,
                "max.in.flight.requests.per.connection": 5,
                "enable.idempotence": True,
                "compression.type": "snappy",
                "linger.ms": 10,
                "batch.size": 16384,
            }
        )
        return config

    @property
    def kafka_consumer_config(self) -> dict:
        """Get Kafka consumer-specific configuration.
        
        Based on ccloud-python-client sample with session.timeout.ms=45000 for stability.
        """
        config = self.kafka_config.copy()
        config.update(
            {
                "group.id": self.kafka_consumer_group_id,
                "auto.offset.reset": "earliest",
                "enable.auto.commit": False,  # Manual commit for safety
                # Best practice for higher availability (recommended for clients prior to librdkafka 1.7)
                "session.timeout.ms": 45000,
                "heartbeat.interval.ms": 10000,
                "max.poll.interval.ms": 300000,
            }
        )
        return config


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
