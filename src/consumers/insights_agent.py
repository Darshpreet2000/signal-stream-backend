"""Insights extraction agent consumer."""

import logging
from typing import Any, Dict

from ..ai import GeminiService
from ..config import Settings
from ..kafka import BaseKafkaConsumer, KafkaProducerService
from ..models import ConversationState

logger = logging.getLogger(__name__)


class InsightsAgentConsumer(BaseKafkaConsumer):
    """Consumer that extracts insights, intent, and urgency."""

    def __init__(
        self,
        settings: Settings,
        producer: KafkaProducerService,
        gemini_service: GeminiService,
    ):
        """Initialize insights agent.

        Args:
            settings: Application settings
            producer: Kafka producer for outputting results
            gemini_service: Gemini AI service
        """
        super().__init__(
            settings=settings,
            topics=[settings.kafka_topic_conversations_state],
            group_id=f"{settings.kafka_consumer_group_id}-insights-agent",
            producer=producer,
        )
        self.producer_service = producer
        self.gemini = gemini_service

    async def process_message(self, message: Dict[str, Any], headers: Dict[str, str]) -> None:
        """Extract insights from conversation.

        Args:
            message: Conversation state
            headers: Message headers
        """
        logger.debug(f"→ [InsightsAgent] Processing message")
        try:
            # Parse conversation state
            conv_state = ConversationState(**message)
            logger.debug(f"  Parsed: conv_id={conv_state.conversation_id}, messages={len(conv_state.recent_messages)}")

            # Get conversation context
            if not conv_state.recent_messages:
                return

            conversation_text = conv_state.get_context_text(max_messages=5)
            logger.debug(f"  Context text length: {len(conversation_text)} chars")

            # Extract insights (now also returns summary)
            logger.debug(f"  Calling gemini.extract_insights...")
            insights_result, summary_result = await self.gemini.extract_insights(
                conversation_id=conv_state.conversation_id,
                tenant_id=conv_state.tenant_id,
                conversation_text=conversation_text,
            )
            logger.debug(f"  ✓ Insights: intent={insights_result.intent.value}, urgency={insights_result.urgency.value}")
            logger.debug(f"  ✓ Summary: {summary_result.tldr[:50]}...")

            # Produce insights result
            logger.debug(f"  Producing to {self.settings.kafka_topic_ai_insights}...")
            await self.producer_service.produce(
                topic=self.settings.kafka_topic_ai_insights,
                value=insights_result.model_dump(mode="json"),
                key=conv_state.conversation_id,
                tenant_id=conv_state.tenant_id,
            )
            
            # Note: Summary generation is now handled by SummaryAgentConsumer iteratively
            # We ignore summary_result here to avoid double-producing

            logger.info(
                f"Insights extracted: {insights_result.intent.value} (urgency: {insights_result.urgency.value})",
                extra={
                    "conversation_id": conv_state.conversation_id,
                    "intent": insights_result.intent.value,
                    "urgency": insights_result.urgency.value,
                },
            )

        except Exception as e:
            logger.error(f"Error in insights agent: {e}", exc_info=True)
            raise
