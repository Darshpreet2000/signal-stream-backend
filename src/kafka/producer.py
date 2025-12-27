"""Kafka producer service for publishing messages."""

import json
import logging
from typing import Any, Dict, Optional
from uuid import uuid4

from confluent_kafka import Producer
from confluent_kafka.admin import AdminClient, NewTopic

from ..config import Settings

logger = logging.getLogger(__name__)


class KafkaProducerService:
    """Kafka producer service with tenant isolation and error handling."""

    def __init__(self, settings: Settings):
        """Initialize Kafka producer.

        Args:
            settings: Application settings with Kafka configuration
        """
        self.settings = settings
        # Use base kafka_config with producer-specific settings added
        producer_config = settings.kafka_config.copy()
        producer_config.update({
            "acks": "all",
            "retries": 3,
            "max.in.flight.requests.per.connection": 5,
            "enable.idempotence": True,
            "compression.type": "snappy",
            "linger.ms": 10,
            "batch.size": 16384,
        })
        self.producer = Producer(producer_config)
        logger.info("Kafka producer initialized")

    async def produce(
        self,
        topic: str,
        value: Dict[str, Any],
        key: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        tenant_id: Optional[str] = None,
    ) -> None:
        """Produce a message to Kafka topic.

        Args:
            topic: Kafka topic name
            value: Message value (will be JSON serialized)
            key: Optional message key for partitioning
            headers: Optional message headers
            tenant_id: Tenant ID for multi-tenancy (added to headers)
        """
        logger.debug(
            f"→ [produce] topic={topic}, key={key}, tenant_id={tenant_id}"
        )
        try:
            # Prepare headers
            message_headers = headers or {}
            if tenant_id:
                message_headers["tenant_id"] = tenant_id
            
            # Add correlation ID for tracing
            message_headers["correlation_id"] = str(uuid4())

            # Serialize value to JSON
            value_bytes = json.dumps(value, default=str).encode("utf-8")
            key_bytes = key.encode("utf-8") if key else None

            # Convert headers to list of tuples
            header_list = [(k, v.encode("utf-8")) for k, v in message_headers.items()]

            # Produce message
            self.producer.produce(
                topic=topic,
                value=value_bytes,
                key=key_bytes,
                headers=header_list,
                callback=self._delivery_callback,
            )

            # Trigger delivery reports
            self.producer.poll(0)

            logger.debug(
                f"Produced message to topic '{topic}'",
                extra={
                    "topic": topic,
                    "key": key,
                    "tenant_id": tenant_id,
                },
            )

        except Exception as e:
            logger.error(
                f"Failed to produce message to topic '{topic}': {e}",
                extra={"topic": topic, "error": str(e)},
                exc_info=True,
            )
            raise

    def _delivery_callback(self, err, msg):
        """Callback for message delivery reports.

        Args:
            err: Error if delivery failed
            msg: Message that was delivered
        """
        if err:
            logger.error(
                f"Message delivery failed: {err}",
                extra={
                    "topic": msg.topic(),
                    "partition": msg.partition(),
                    "error": str(err),
                },
            )
        else:
            logger.debug(
                f"Message delivered to {msg.topic()} [{msg.partition()}] @ {msg.offset()}",
                extra={
                    "topic": msg.topic(),
                    "partition": msg.partition(),
                    "offset": msg.offset(),
                },
            )

    async def flush(self, timeout: float = 10.0) -> None:
        """Flush pending messages.

        Args:
            timeout: Maximum time to wait in seconds
        """
        remaining = self.producer.flush(timeout=timeout)
        if remaining > 0:
            logger.warning(
                f"{remaining} messages were not delivered within timeout",
                extra={"remaining_messages": remaining},
            )
        else:
            logger.info("All pending messages flushed successfully")

    async def close(self) -> None:
        """Close the producer and flush pending messages."""
        logger.info("Closing Kafka producer...")
        await self.flush()
        logger.info("Kafka producer closed")
