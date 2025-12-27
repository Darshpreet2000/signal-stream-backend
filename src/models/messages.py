"""Message models and schemas."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class MessageSender(str, Enum):
    """Message sender type."""

    CUSTOMER = "customer"
    AGENT = "agent"
    SYSTEM = "system"


class MessageChannel(str, Enum):
    """Communication channel."""

    CHAT = "chat"
    EMAIL = "email"
    VOICE = "voice"
    SMS = "sms"


class CreateMessageRequest(BaseModel):
    """Request model for creating a new support message."""

    conversation_id: str = Field(
        ..., description="Unique identifier for the conversation"
    )
    sender: MessageSender = Field(..., description="Who sent the message")
    message: str = Field(..., min_length=1, max_length=10000, description="Message content")
    channel: MessageChannel = Field(default=MessageChannel.CHAT, description="Channel type")
    tenant_id: Optional[str] = Field(
        default=None, description="Tenant ID (optional, can be derived from auth)"
    )
    metadata: Optional[dict] = Field(default=None, description="Additional metadata")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "conversation_id": "conv_123abc",
                    "sender": "customer",
                    "message": "I'm having trouble with my recent order #12345",
                    "channel": "chat",
                    "tenant_id": "acme-corp",
                }
            ]
        }
    }


class CreateMessageResponse(BaseModel):
    """Response model for message creation."""

    message_id: UUID = Field(..., description="Unique message identifier")
    conversation_id: str = Field(..., description="Conversation identifier")
    status: str = Field(default="accepted", description="Processing status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Server timestamp")


class SupportMessage(BaseModel):
    """Internal support message model (written to Kafka)."""

    message_id: UUID = Field(default_factory=uuid4, description="Unique message ID")
    conversation_id: str = Field(..., description="Conversation ID")
    tenant_id: str = Field(..., description="Tenant ID")
    sender: MessageSender = Field(..., description="Message sender")
    message: str = Field(..., description="Message content")
    channel: MessageChannel = Field(..., description="Communication channel")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    metadata: Optional[dict] = Field(default=None, description="Additional metadata")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message_id": "550e8400-e29b-41d4-a716-446655440000",
                    "conversation_id": "conv_123abc",
                    "tenant_id": "acme-corp",
                    "sender": "customer",
                    "message": "I need help with my account",
                    "channel": "chat",
                    "timestamp": "2025-12-25T10:30:00Z",
                }
            ]
        }
    }
