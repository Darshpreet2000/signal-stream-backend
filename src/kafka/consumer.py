"""Base Kafka consumer with error handling and graceful shutdown."""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from confluent_kafka import Consumer, KafkaError, KafkaException, Message

from ..config import Settings
from .producer import KafkaProducerService

logger = logging.getLogger(__name__)


class BaseKafkaConsumer(ABC):
    """Base class for Kafka consumers with DLQ pattern and graceful shutdown."""

    def __init__(
        self,
        settings: Settings,
        topics: List[str],
        group_id: Optional[str] = None,
        producer: Optional[KafkaProducerService] = None,
    ):
        """Initialize base consumer.

        Args:
            settings: Application settings
            topics: List of topics to subscribe to
            group_id: Consumer group ID (overrides settings if provided)
            producer: Producer service for DLQ (optional)
        """
        self.settings = settings
        self.topics = topics
        self.producer = producer
        self.running = False
        self.max_retries = 3

        # Configure consumer (matches ccloud-python-client pattern)
        consumer_config = settings.kafka_config.copy()
        consumer_config["group.id"] = group_id or settings.kafka_consumer_group_id
        consumer_config["auto.offset.reset"] = "earliest"
        consumer_config["enable.auto.commit"] = False  # Manual commit for safety
        consumer_config["session.timeout.ms"] = 45000
        consumer_config["heartbeat.interval.ms"] = 10000
        consumer_config["max.poll.interval.ms"] = 300000

        self.consumer = Consumer(consumer_config)
        logger.info(
            f"Consumer initialized for topics: {topics}",
            extra={"topics": topics, "group_id": consumer_config["group.id"]},
        )

    @abstractmethod
    async def process_message(self, message: Dict[str, Any], headers: Dict[str, str]) -> None:
        """Process a single message. Must be implemented by subclasses.

        Args:
            message: Deserialized message value
            headers: Message headers
        """
        pass

    def _parse_message(self, msg: Message) -> tuple[Dict[str, Any], Dict[str, str]]:
        """Parse Kafka message into value and headers.

        Args:
            msg: Kafka message

        Returns:
            Tuple of (value dict, headers dict)
        """
        # Parse value
        value = json.loads(msg.value().decode("utf-8"))

        # Parse headers
        headers = {}
        if msg.headers():
            headers = {k: v.decode("utf-8") for k, v in msg.headers()}

        return value, headers

    async def _handle_message(self, msg: Message) -> bool:
        """Handle a single message with retry logic.

        Args:
            msg: Kafka message

        Returns:
            True if processing succeeded, False otherwise
        """
        retry_count = 0
        last_error = None

        while retry_count < self.max_retries:
            try:
                # Parse message
                value, headers = self._parse_message(msg)

                # Get retry count from headers
                if "retry_count" in headers:
                    retry_count = int(headers["retry_count"])

                # Process message
                await self.process_message(value, headers)

                logger.debug(
                    f"Successfully processed message from {msg.topic()}",
                    extra={
                        "topic": msg.topic(),
                        "partition": msg.partition(),
                        "offset": msg.offset(),
                    },
                )
                return True

            except Exception as e:
                retry_count += 1
                last_error = e
                logger.warning(
                    f"Error processing message (attempt {retry_count}/{self.max_retries}): {e}",
                    extra={
                        "topic": msg.topic(),
                        "partition": msg.partition(),
                        "offset": msg.offset(),
                        "retry_count": retry_count,
                        "error": str(e),
                    },
                )

                if retry_count < self.max_retries:
                    # Exponential backoff
                    await asyncio.sleep(2**retry_count)

        # All retries exhausted - send to DLQ
        if self.producer:
            await self._send_to_dlq(msg, last_error)

        return False

    async def _send_to_dlq(self, msg: Message, error: Exception) -> None:
        """Send failed message to Dead Letter Queue.

        Args:
            msg: Original Kafka message
            error: Exception that caused the failure
        """
        try:
            value, headers = self._parse_message(msg)

            # Add error information
            dlq_message = {
                "original_topic": msg.topic(),
                "original_partition": msg.partition(),
                "original_offset": msg.offset(),
                "value": value,
                "error": str(error),
                "error_type": type(error).__name__,
            }

            # Add DLQ-specific headers
            headers["dlq_source_topic"] = msg.topic()
            headers["dlq_error"] = str(error)

            await self.producer.produce(
                topic=self.settings.kafka_topic_dlq,
                value=dlq_message,
                key=msg.key().decode("utf-8") if msg.key() else None,
                headers=headers,
            )

            logger.error(
                f"Message sent to DLQ after {self.max_retries} retries",
                extra={
                    "original_topic": msg.topic(),
                    "dlq_topic": self.settings.kafka_topic_dlq,
                    "error": str(error),
                },
            )

        except Exception as dlq_error:
            logger.critical(
                f"Failed to send message to DLQ: {dlq_error}",
                extra={"error": str(dlq_error)},
                exc_info=True,
            )

    async def start(self) -> None:
        """Start consuming messages."""
        self.running = True
        loop = asyncio.get_running_loop()
        
        # Subscribe in executor to avoid blocking
        await loop.run_in_executor(None, self.consumer.subscribe, self.topics)

        logger.info(
            f"Consumer started for topics: {self.topics}",
            extra={"topics": self.topics},
        )

        try:
            while self.running:
                # Poll for messages (non-blocking via executor)
                # We use a small timeout in poll to avoid busy waiting if we were in a thread,
                # but since we are in asyncio, we want to yield.
                # Running poll in executor ensures we don't block the loop even for a millisecond.
                msg = await loop.run_in_executor(None, self.consumer.poll, 0.1)

                if msg is None:
                    await asyncio.sleep(0.1)  # Yield control if no message
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        # End of partition - not an error
                        continue
                    else:
                        logger.error(f"Consumer error: {msg.error()}")
                        continue

                # Process message
                success = await self._handle_message(msg)

                # Commit offset only if processing succeeded
                if success:
                    try:
                        # Commit in executor to avoid blocking
                        await loop.run_in_executor(
                            None, 
                            lambda: self.consumer.commit(message=msg, asynchronous=False)
                        )
                    except KafkaException as e:
                        logger.error(f"Failed to commit offset: {e}")

                # Small delay to prevent CPU spinning and allow other tasks to run
                await asyncio.sleep(0.01)

        except Exception as e:
            logger.error(f"Consumer loop error: {e}", exc_info=True)
            raise

        finally:
            await self.stop()

    async def stop(self) -> None:
        """Stop consuming and close consumer gracefully."""
        if not self.running:
            return

        logger.info("Stopping consumer...")
        self.running = False

        try:
            # Commit final offsets
            self.consumer.commit(asynchronous=False)
            logger.info("Final offsets committed")
        except Exception as e:
            logger.error(f"Error committing final offsets: {e}")

        try:
            # Close consumer
            self.consumer.close()
            logger.info("Consumer closed successfully")
        except Exception as e:
            logger.error(f"Error closing consumer: {e}")
