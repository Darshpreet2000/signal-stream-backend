"""Conversation state models."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from .messages import SupportMessage
from .intelligence import SummaryResult


class ConversationState(BaseModel):
    """Conversation state with rolling message window."""

    conversation_id: str
    tenant_id: str
    message_count: int = 0
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    recent_messages: List[SupportMessage] = Field(default_factory=list, max_length=10)
    participants: List[str] = Field(default_factory=list)
    summary: Optional[SummaryResult] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def add_message(self, message: SupportMessage) -> None:
        """Add a message to the conversation state."""
        self.recent_messages.append(message)
        # Keep only last 10 messages
        if len(self.recent_messages) > 10:
            self.recent_messages = self.recent_messages[-10:]
        
        self.message_count += 1
        self.last_activity = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        # Track participants
        sender_type = message.sender.value
        if sender_type not in self.participants:
            self.participants.append(sender_type)

    def get_context_text(self, max_messages: int = 5) -> str:
        """Get formatted conversation context for AI processing."""
        messages = self.recent_messages[-max_messages:]
        context_lines = []
        
        for msg in messages:
            sender_label = msg.sender.value.capitalize()
            context_lines.append(f"{sender_label}: {msg.message}")
        
        return "\n".join(context_lines)
