"""Conversation processor consumer - builds conversation state."""

import logging
from typing import Any, Dict

from ..config import Settings
from ..kafka import BaseKafkaConsumer, KafkaProducerService
from ..models import SupportMessage, ConversationState, SummaryResult
from ..ai.mock_intelligence import MockIntelligenceService

logger = logging.getLogger(__name__)


class ConversationProcessorConsumer(BaseKafkaConsumer):
    """Consumer that builds conversation state from raw messages and summaries."""

    def __init__(self, settings: Settings, producer: KafkaProducerService):
        """Initialize conversation processor.

        Args:
            settings: Application settings
            producer: Kafka producer for outputting conversation state
        """
        super().__init__(
            settings=settings,
            topics=[settings.kafka_topic_messages_raw, settings.kafka_topic_ai_summary],
            group_id=f"{settings.kafka_consumer_group_id}-conversation-processor",
            producer=producer,
        )
        self.producer_service = producer

        # In-memory conversation state cache (in production, use Redis)
        self.conversation_cache: Dict[str, ConversationState] = {}
        
        # Mock intelligence service for testing
        self.mock_service = MockIntelligenceService()
        
        if settings.enable_mock_mode:
            logger.warning("🧪 MOCK MODE ENABLED - Using hardcoded intelligence data for testing")

    async def process_message(self, message: Dict[str, Any], headers: Dict[str, str]) -> None:
        """Process raw message or summary and update conversation state.

        Args:
            message: Raw support message or summary result
            headers: Message headers
        """
        try:
            # Detect message type using duck typing
            if "tldr" in message and "customer_issue" in message:
                # It's a summary result - skip in mock mode
                if self.settings.enable_mock_mode:
                    return
                    
                summary = SummaryResult(**message)
                cache_key = f"{summary.tenant_id}:{summary.conversation_id}"
                
                if cache_key in self.conversation_cache:
                    # Update the summary in the cached state
                    self.conversation_cache[cache_key].summary = summary
                    logger.debug(
                        f"Updated summary for {summary.conversation_id}",
                        extra={"conversation_id": summary.conversation_id}
                    )
                # Don't produce state update to avoid triggering agents again
                return
            
            # It's a raw message
            support_message = SupportMessage(**message)
            
            # ===== MOCK MODE =====
            if self.settings.enable_mock_mode:
                await self._process_message_mock_mode(support_message)
                return
            
            # ===== REAL MODE (original processing logic) =====
            await self._process_message_real_mode(support_message)

        except Exception as e:
            logger.error(f"Error processing conversation message: {e}", exc_info=True)
            raise

    async def _process_message_real_mode(self, support_message: SupportMessage) -> None:
        """Original processing logic - can be uncommented to restore real mode.
        
        Args:
            support_message: The support message to process
        """
        # Get or create conversation state
        cache_key = f"{support_message.tenant_id}:{support_message.conversation_id}"

        if cache_key not in self.conversation_cache:
            self.conversation_cache[cache_key] = ConversationState(
                conversation_id=support_message.conversation_id,
                tenant_id=support_message.tenant_id,
            )

        conv_state = self.conversation_cache[cache_key]

        # Update conversation state
        conv_state.add_message(support_message)

        # Produce updated state (only for new messages, not summaries)
        await self.producer_service.produce(
            topic=self.settings.kafka_topic_conversations_state,
            value=conv_state.model_dump(mode="json"),
            key=support_message.conversation_id,
            tenant_id=support_message.tenant_id,
        )

        logger.info(
            f"Updated conversation state for {support_message.conversation_id}",
            extra={
                "conversation_id": support_message.conversation_id,
                "message_count": conv_state.message_count,
            },
        )
    
    async def _process_message_mock_mode(self, support_message: SupportMessage) -> None:
        """Mock mode - returns hardcoded intelligence data for testing.
        
        Args:
            support_message: The support message to process
        """
        logger.debug(f"🧪 [MOCK MODE] Processing message: {support_message.message[:50]}...")
        
        # Generate mock intelligence data
        mock_data = self.mock_service.get_mock_intelligence(
            conversation_id=support_message.conversation_id,
            tenant_id=support_message.tenant_id,
            message_text=support_message.message,
            sender=support_message.sender.value
        )
        
        # Produce directly to aggregated topic (skip all agent processing)
        await self.producer_service.produce(
            topic=self.settings.kafka_topic_ai_aggregated,
            value=mock_data,
            key=support_message.conversation_id,
            tenant_id=support_message.tenant_id,
        )
        
        logger.info(
            f"🧪 [MOCK MODE] Published mock intelligence for {support_message.conversation_id}",
            extra={"conversation_id": support_message.conversation_id}
        )
