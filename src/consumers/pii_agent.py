"""PII detection agent consumer."""

import logging
from typing import Any, Dict

from ..ai import GeminiService
from ..config import Settings
from ..kafka import BaseKafkaConsumer, KafkaProducerService
from ..models import ConversationState

logger = logging.getLogger(__name__)


class PIIAgentConsumer(BaseKafkaConsumer):
    """Consumer that detects PII in conversations."""

    def __init__(
        self,
        settings: Settings,
        producer: KafkaProducerService,
        gemini_service: GeminiService,
    ):
        """Initialize PII agent.

        Args:
            settings: Application settings
            producer: Kafka producer for outputting results
            gemini_service: Gemini AI service
        """
        super().__init__(
            settings=settings,
            topics=[settings.kafka_topic_conversations_state],
            group_id=f"{settings.kafka_consumer_group_id}-pii-agent",
            producer=producer,
        )
        self.producer_service = producer
        self.gemini = gemini_service

    async def process_message(self, message: Dict[str, Any], headers: Dict[str, str]) -> None:
        """Detect PII in conversation.

        Args:
            message: Conversation state
            headers: Message headers
        """
        logger.debug(f"→ [PIIAgent] Processing message")
        try:
            # Parse conversation state
            conv_state = ConversationState(**message)
            logger.debug(f"  Parsed: conv_id={conv_state.conversation_id}, messages={len(conv_state.recent_messages)}")

            # Get last message for PII detection
            if not conv_state.recent_messages:
                return

            last_message = conv_state.recent_messages[-1]

            # Detect PII
            logger.debug(f"  Calling gemini.detect_pii...")
            pii_result = await self.gemini.detect_pii(
                conversation_id=conv_state.conversation_id,
                tenant_id=conv_state.tenant_id,
                message_text=last_message.message,
            )
            logger.debug(f"  ✓ PII result: has_pii={pii_result.has_pii}, entities={len(pii_result.entities)}")

            # Produce PII result
            logger.debug(f"  Producing to {self.settings.kafka_topic_ai_pii}...")
            await self.producer_service.produce(
                topic=self.settings.kafka_topic_ai_pii,
                value=pii_result.model_dump(mode="json"),
                key=conv_state.conversation_id,
                tenant_id=conv_state.tenant_id,
            )

            logger.info(
                f"PII detection completed: has_pii={pii_result.has_pii}",
                extra={
                    "conversation_id": conv_state.conversation_id,
                    "has_pii": pii_result.has_pii,
                    "entity_count": len(pii_result.entities),
                },
            )

        except Exception as e:
            logger.error(f"Error in PII agent: {e}", exc_info=True)
            raise
