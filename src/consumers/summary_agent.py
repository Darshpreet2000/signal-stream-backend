"""Summary generation agent consumer."""

import logging
from typing import Any, Dict, Optional

from ..ai import GeminiService
from ..config import Settings
from ..kafka import BaseKafkaConsumer, KafkaProducerService
from ..models import ConversationState, SummaryResult

logger = logging.getLogger(__name__)


class SummaryAgentConsumer(BaseKafkaConsumer):
    """Consumer that generates conversation summaries using full conversation history."""

    def __init__(
        self,
        settings: Settings,
        producer: KafkaProducerService,
        gemini_service: GeminiService,
    ):
        """Initialize summary agent.

        Args:
            settings: Application settings
            producer: Kafka producer for outputting results
            gemini_service: Gemini AI service
        """
        super().__init__(
            settings=settings,
            topics=[settings.kafka_topic_conversations_state],
            group_id=f"{settings.kafka_consumer_group_id}-summary-agent",
            producer=producer,
        )
        self.producer_service = producer
        self.gemini = gemini_service

    async def process_message(self, message: Dict[str, Any], headers: Dict[str, str]) -> None:
        """Generate conversation summary using previous summary + new message.

        Args:
            message: Conversation state
            headers: Message headers
        """
        logger.debug(f"→ [SummaryAgent] Processing message")
        try:
            # Parse conversation state
            conv_state = ConversationState(**message)
            logger.debug(f"  Parsed: conv_id={conv_state.conversation_id}, messages={len(conv_state.recent_messages)}")

            if not conv_state.recent_messages:
                return

            # Get the latest message and old summary
            last_message = conv_state.recent_messages[-1]
            old_summary = conv_state.summary

            # Generate updated summary
            logger.debug(f"  Calling gemini.update_conversation_summary...")
            summary_result = await self.gemini.update_conversation_summary(
                conversation_id=conv_state.conversation_id,
                tenant_id=conv_state.tenant_id,
                old_summary=old_summary,
                new_message=last_message.message,
                sender=last_message.sender.value,
            )
            logger.debug(f"  ✓ New Summary: {summary_result.tldr[:60]}...")

            # Produce summary result
            logger.debug(f"  Producing to {self.settings.kafka_topic_ai_summary}...")
            await self.producer_service.produce(
                topic=self.settings.kafka_topic_ai_summary,
                value=summary_result.model_dump(mode="json"),
                key=conv_state.conversation_id,
                tenant_id=conv_state.tenant_id,
            )

            logger.info(
                f"Summary updated: {summary_result.tldr[:50]}...",
                extra={"conversation_id": conv_state.conversation_id},
            )

        except Exception as e:
            logger.error(f"Error in summary agent: {e}", exc_info=True)
            raise
