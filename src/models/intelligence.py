"""AI intelligence result models."""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SentimentType(str, Enum):
    """Sentiment classification."""

    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class EmotionType(str, Enum):
    """Emotion classification."""

    ANGRY = "angry"
    FRUSTRATED = "frustrated"
    SATISFIED = "satisfied"
    CONFUSED = "confused"
    URGENT = "urgent"
    HAPPY = "happy"
    NEUTRAL = "neutral"


class SentimentResult(BaseModel):
    """Sentiment analysis result."""

    conversation_id: str
    tenant_id: str
    sentiment: SentimentType
    confidence: float = Field(ge=0.0, le=1.0)
    emotion: EmotionType
    reasoning: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PIIEntityType(str, Enum):
    """Types of PII entities."""

    EMAIL = "email"
    PHONE = "phone"
    CREDIT_CARD = "credit_card"
    SSN = "ssn"
    ADDRESS = "address"
    ACCOUNT_NUMBER = "account_number"
    NAME = "name"


class PIIEntity(BaseModel):
    """Detected PII entity."""

    type: PIIEntityType
    value: str = "[REDACTED]"
    start_index: int
    end_index: int


class PIIResult(BaseModel):
    """PII detection result."""

    conversation_id: str
    tenant_id: str
    has_pii: bool
    entities: List[PIIEntity] = Field(default_factory=list)
    redacted_text: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class IntentType(str, Enum):
    """Customer intent classification."""

    REFUND_REQUEST = "Refund Request"
    TECHNICAL_ISSUE = "Technical Issue"
    BILLING_INQUIRY = "Billing Inquiry"
    FEATURE_REQUEST = "Feature Request"
    COMPLAINT = "Complaint"
    GENERAL_INQUIRY = "General Inquiry"
    ACCOUNT_ISSUE = "Account Issue"
    CANCELLATION = "Cancellation"


class UrgencyLevel(str, Enum):
    """Urgency classification."""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class InsightsResult(BaseModel):
    """Intent and insights extraction result."""

    conversation_id: str
    tenant_id: str
    intent: IntentType
    urgency: UrgencyLevel
    categories: List[str] = Field(default_factory=list)
    suggested_actions: List[str] = Field(default_factory=list)
    requires_escalation: bool
    estimated_resolution_time: str
    key_concerns: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SummaryResult(BaseModel):
    """Conversation summary result."""

    conversation_id: str
    tenant_id: str
    tldr: str
    customer_issue: str
    agent_response: Optional[str] = None
    key_points: List[str] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AggregatedIntelligence(BaseModel):
    """Aggregated intelligence from all AI agents."""

    conversation_id: str
    tenant_id: str
    sentiment: Optional[SentimentResult] = None
    pii: Optional[PIIResult] = None
    insights: Optional[InsightsResult] = None
    summary: Optional[SummaryResult] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "conversation_id": "conv_123abc",
                    "tenant_id": "acme-corp",
                    "sentiment": {
                        "sentiment": "negative",
                        "confidence": 0.87,
                        "emotion": "frustrated",
                        "reasoning": "Customer expressing dissatisfaction with service",
                    },
                    "insights": {
                        "intent": "refund_request",
                        "urgency": "high",
                        "requires_escalation": False,
                    },
                    "pii": {"has_pii": True, "entities": [{"type": "email"}]},
                }
            ]
        }
    }
