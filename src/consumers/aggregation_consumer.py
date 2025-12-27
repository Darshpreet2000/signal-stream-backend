"""Aggregation consumer - combines all AI agent outputs."""

import logging
from typing import Any, Dict

from ..config import Settings
from ..kafka import BaseKafkaConsumer, KafkaProducerService
from ..api.websocket import broadcast_intelligence
from ..models import (
    AggregatedIntelligence,
    SentimentResult,
    PIIResult,
    InsightsResult,
    SummaryResult,
)

logger = logging.getLogger(__name__)


class AggregationConsumer(BaseKafkaConsumer):
    """Consumer that aggregates all AI agent outputs."""

    def __init__(self, settings: Settings, producer: KafkaProducerService):
        """Initialize aggregation consumer.

        Args:
            settings: Application settings
            producer: Kafka producer for outputting aggregated intelligence
        """
        # Subscribe to all AI agent topics
        topics = [
            settings.kafka_topic_ai_sentiment,
            settings.kafka_topic_ai_pii,
            settings.kafka_topic_ai_insights,
            settings.kafka_topic_ai_summary,
        ]

        super().__init__(
            settings=settings,
            topics=topics,
            group_id=f"{settings.kafka_consumer_group_id}-aggregation",
            producer=producer,
        )
        self.producer_service = producer

        # In-memory cache of aggregated intelligence
        self.intelligence_cache: Dict[str, AggregatedIntelligence] = {}

    async def process_message(self, message: Dict[str, Any], headers: Dict[str, str]) -> None:
        """Aggregate AI agent output.

        Args:
            message: AI agent result
            headers: Message headers (contains source topic)
        """
        try:
            # Determine which AI agent produced this message
            # We need to track the topic, but it's not in headers
            # Let's infer from message structure

            conversation_id = message.get("conversation_id")
            tenant_id = message.get("tenant_id")

            if not conversation_id or not tenant_id:
                logger.warning("Message missing conversation_id or tenant_id")
                return

            # Get or create aggregated intelligence
            cache_key = f"{tenant_id}:{conversation_id}"

            if cache_key not in self.intelligence_cache:
                self.intelligence_cache[cache_key] = AggregatedIntelligence(
                    conversation_id=conversation_id,
                    tenant_id=tenant_id,
                )

            agg_intel = self.intelligence_cache[cache_key]

            # Update the appropriate field based on message structure
            if "sentiment" in message and "emotion" in message:
                agg_intel.sentiment = SentimentResult(**message)
            elif "has_pii" in message and "entities" in message:
                new_pii = PIIResult(**message)
                
                # Persist PII detection state
                if agg_intel.pii:
                    # If PII was ever detected, keep the flag true
                    if agg_intel.pii.has_pii:
                        new_pii.has_pii = True
                    
                    # Merge entities to show all detected PII across conversation
                    # We use a simple deduplication based on value and type
                    existing_keys = {(e.type, e.value) for e in agg_intel.pii.entities}
                    
                    combined_entities = list(agg_intel.pii.entities)
                    for entity in new_pii.entities:
                        if (entity.type, entity.value) not in existing_keys:
                            combined_entities.append(entity)
                            existing_keys.add((entity.type, entity.value))
                            
                    new_pii.entities = combined_entities
                
                agg_intel.pii = new_pii
            elif "intent" in message and "urgency" in message:
                agg_intel.insights = InsightsResult(**message)
            elif "tldr" in message and "customer_issue" in message:
                agg_intel.summary = SummaryResult(**message)

            # Update timestamp
            from datetime import datetime
            agg_intel.last_updated = datetime.utcnow()

            # Produce aggregated intelligence
            await self.producer_service.produce(
                topic=self.settings.kafka_topic_ai_aggregated,
                value=agg_intel.model_dump(mode="json"),
                key=conversation_id,
                tenant_id=tenant_id,
            )

            logger.info(
                f"Aggregated intelligence updated for {conversation_id}",
                extra={
                    "conversation_id": conversation_id,
                    "has_sentiment": agg_intel.sentiment is not None,
                    "has_pii": agg_intel.pii is not None,
                    "has_insights": agg_intel.insights is not None,
                    "has_summary": agg_intel.summary is not None,
                },
            )

            # Push real-time updates to WebSocket clients only when ALL agents have completed
            all_complete = (
                agg_intel.sentiment is not None
                and agg_intel.pii is not None
                and agg_intel.insights is not None
                and agg_intel.summary is not None
            )
            
            if all_complete:
                logger.debug(f"All 4 agents completed for {conversation_id}, broadcasting to WebSocket clients")
                await broadcast_intelligence(conversation_id, agg_intel)
            else:
                logger.debug(f"Waiting for more agents to complete before broadcasting (S:{agg_intel.sentiment is not None} P:{agg_intel.pii is not None} I:{agg_intel.insights is not None} Su:{agg_intel.summary is not None})")

        except Exception as e:
            logger.error(f"Error in aggregation consumer: {e}", exc_info=True)
            raise
