"""Kafka admin operations."""

import asyncio
import logging
from typing import List

from confluent_kafka.admin import AdminClient, NewTopic

from ..config import Settings

logger = logging.getLogger(__name__)


class KafkaAdminService:
    """Kafka admin service for topic management."""

    def __init__(self, settings: Settings):
        """Initialize Kafka admin client.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.admin_client = AdminClient(settings.kafka_config)
        logger.info("Kafka admin client initialized")

    async def create_topics(
        self,
        topics: List[str],
        num_partitions: int = 3,
        replication_factor: int = 3,
    ) -> None:
        """Create Kafka topics if they don't exist.

        Args:
            topics: List of topic names to create
            num_partitions: Number of partitions per topic
            replication_factor: Replication factor for topics
        """
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            self._create_topics_sync,
            topics,
            num_partitions,
            replication_factor,
        )

    def _create_topics_sync(
        self,
        topics: List[str],
        num_partitions: int = 3,
        replication_factor: int = 3,
    ) -> None:
        """Synchronous implementation of create_topics."""
        # Get existing topics
        metadata = self.admin_client.list_topics(timeout=10)
        existing_topics = set(metadata.topics.keys())

        # Filter out topics that already exist
        topics_to_create = [t for t in topics if t not in existing_topics]

        if not topics_to_create:
            logger.info("All topics already exist")
            return

        # Create new topics with 5 minute retention
        new_topics = [
            NewTopic(
                topic=topic,
                num_partitions=num_partitions,
                replication_factor=replication_factor,
                config={
                    'retention.ms': '300000',  # 5 minutes
                    'cleanup.policy': 'delete'
                }
            )
            for topic in topics_to_create
        ]

        # Create topics
        fs = self.admin_client.create_topics(new_topics)

        # Wait for operation to complete
        for topic, f in fs.items():
            try:
                f.result()  # Block until topic is created
                logger.info(f"Topic '{topic}' created successfully")
            except Exception as e:
                logger.error(f"Failed to create topic '{topic}': {e}")

    async def ensure_topics_exist(self) -> None:
        """Ensure all required topics exist."""
        required_topics = [
            self.settings.kafka_topic_messages_raw,
            self.settings.kafka_topic_conversations_state,
            self.settings.kafka_topic_ai_sentiment,
            self.settings.kafka_topic_ai_pii,
            self.settings.kafka_topic_ai_insights,
            self.settings.kafka_topic_ai_summary,
            self.settings.kafka_topic_ai_aggregated,
            self.settings.kafka_topic_dlq,
        ]

        logger.info(f"Ensuring {len(required_topics)} topics exist...")
        await self.create_topics(required_topics)
        logger.info("All required topics verified")
