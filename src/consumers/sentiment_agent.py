"""Sentiment analysis agent consumer."""

import logging
from typing import Any, Dict

from ..ai import GeminiService
from ..config import Settings
from ..kafka import BaseKafkaConsumer, KafkaProducerService
from ..models import ConversationState

logger = logging.getLogger(__name__)


class SentimentAgentConsumer(BaseKafkaConsumer):
    """Consumer that performs sentiment analysis on conversations."""

    def __init__(
        self,
        settings: Settings,
        producer: KafkaProducerService,
        gemini_service: GeminiService,
    ):
        """Initialize sentiment agent.

        Args:
            settings: Application settings
            producer: Kafka producer for outputting results
            gemini_service: Gemini AI service
        """
        super().__init__(
            settings=settings,
            topics=[settings.kafka_topic_conversations_state],
            group_id=f"{settings.kafka_consumer_group_id}-sentiment-agent",
            producer=producer,
        )
        self.producer_service = producer
        self.gemini = gemini_service

    async def process_message(self, message: Dict[str, Any], headers: Dict[str, str]) -> None:
        """Analyze sentiment of conversation based on customer messages only.

        Args:
            message: Conversation state
            headers: Message headers
        """
        logger.debug(f"→ [SentimentAgent] Processing message")
        try:
            # Parse conversation state
            conv_state = ConversationState(**message)
            logger.debug(f"  Parsed: conv_id={conv_state.conversation_id}, messages={len(conv_state.recent_messages)}")

            if not conv_state.recent_messages:
                return

            last_message = conv_state.recent_messages[-1]
            
            # Only analyze sentiment when customer sends a message
            if last_message.sender.value != "customer":
                logger.debug(f"  Skipping: Last message from {last_message.sender.value}, not customer")
                return
            
            # Build full conversation context with both customer and agent messages
            # This helps AI understand the flow and why sentiment might change
            if conv_state.summary and conv_state.summary.tldr and len(conv_state.recent_messages) > 1:
                # Use summary for background + recent conversation
                recent_conversation = "\n".join([
                    f"{msg.sender.value.upper()}: {msg.message}" 
                    for msg in conv_state.recent_messages[-5:]  # Last 5 messages
                ])
                context = f"""Background Context: {conv_state.summary.tldr}

Recent Conversation:
{recent_conversation}

IMPORTANT: Analyze the CUSTOMER's CURRENT emotional state based on their latest message above.
"""
            else:
                # No summary yet, use all recent messages
                full_conversation = "\n".join([
                    f"{msg.sender.value.upper()}: {msg.message}" 
                    for msg in conv_state.recent_messages
                ])
                context = f"""Conversation:
{full_conversation}

IMPORTANT: Analyze the CUSTOMER's CURRENT emotional state based on their latest message above.
"""

            # Analyze sentiment
            logger.debug(f"  Calling gemini.analyze_sentiment with full conversation context...")
            sentiment_result = await self.gemini.analyze_sentiment(
                conversation_id=conv_state.conversation_id,
                tenant_id=conv_state.tenant_id,
                message_text=context,
            )
            logger.debug(f"  ✓ Sentiment result: {sentiment_result.sentiment.value}")

            # Produce sentiment result
            logger.debug(f"  Producing to {self.settings.kafka_topic_ai_sentiment}...")
            await self.producer_service.produce(
                topic=self.settings.kafka_topic_ai_sentiment,
                value=sentiment_result.model_dump(mode="json"),
                key=conv_state.conversation_id,
                tenant_id=conv_state.tenant_id,
            )

            logger.info(
                f"Sentiment analysis completed: {sentiment_result.sentiment.value}",
                extra={
                    "conversation_id": conv_state.conversation_id,
                    "sentiment": sentiment_result.sentiment.value,
                    "confidence": sentiment_result.confidence,
                },
            )

        except Exception as e:
            logger.error(f"Error in sentiment agent: {e}", exc_info=True)
            raise
