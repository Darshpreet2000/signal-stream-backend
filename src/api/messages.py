"""Messages API - Producer endpoint for ingesting support messages."""

import asyncio
import logging
from datetime import datetime
from uuid import uuid4

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status

from ..config import Settings, get_settings
from ..kafka import KafkaProducerService
from ..models import (
    CreateMessageRequest,
    CreateMessageResponse,
    SupportMessage,
)
from ..models import AggregatedIntelligence
from ..api.websocket import broadcast_intelligence

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/messages", tags=["messages"])


def get_producer(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> Optional[KafkaProducerService]:
    """Dependency to get Kafka producer.

    In development/demo mode, Kafka may be disabled; in that case return None and let the
    handler use the in-process shortcut.
    """
    producer = getattr(request.app.state, "producer", None)
    if producer is None:
        if settings.app_env == "development" or not settings.kafka_is_configured:
            return None

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Kafka producer is initializing. Please try again in a moment.",
        )
    return producer


@router.post(
    "",
    response_model=CreateMessageResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest Support Message",
    description="Submit a support message to the platform. Messages are processed asynchronously.",
)
async def create_message(
    payload: CreateMessageRequest,
    http_request: Request,
    producer: Optional[KafkaProducerService] = Depends(get_producer),
    settings: Settings = Depends(get_settings),
) -> CreateMessageResponse:
    """Create a new support message.

    This is the primary ingestion endpoint for customer applications.
    Messages are written to Kafka and processed by AI agents asynchronously.

    Args:
        request: Message creation request
        producer: Kafka producer service
        settings: Application settings

    Returns:
        Message creation response with message ID
    """
    try:
        # Generate message ID
        message_id = uuid4()

        # Determine tenant ID
        tenant_id = payload.tenant_id or settings.default_tenant_id

        # Create support message
        support_message = SupportMessage(
            message_id=message_id,
            conversation_id=payload.conversation_id,
            tenant_id=tenant_id,
            sender=payload.sender,
            message=payload.message,
            channel=payload.channel,
            timestamp=datetime.utcnow(),
            metadata=payload.metadata,
        )

        # Produce to Kafka (if enabled/available)
        if producer is not None:
            logger.debug(
                f"  Producing to Kafka topic={settings.kafka_topic_messages_raw}"
            )
            await producer.produce(
                topic=settings.kafka_topic_messages_raw,
                value=support_message.model_dump(mode="json"),
                key=payload.conversation_id,
                tenant_id=tenant_id,
            )
            logger.debug("  ✓ Message produced to Kafka successfully")
            
            # Skip DEV MODE when Kafka is working to avoid duplicate processing
            if settings.app_env == "development":
                logger.debug("  ⚡ Kafka consumers will process this message (skipping DEV MODE)")
        else:
            logger.warning(
                "Kafka producer unavailable; skipping Kafka publish and relying on dev shortcut (if enabled)."
            )

        # Development-mode shortcut: compute and broadcast intelligence directly.
        # This keeps the demo responsive even if Kafka consumers are delayed/unavailable.
        # Only run if Kafka producer is unavailable (to avoid duplicate processing).
        if settings.app_env == "development" and producer is None:
            logger.debug(f"  DEV MODE: Computing intelligence in-process")
            conversation_id = payload.conversation_id
            cache_key = f"{tenant_id}:{conversation_id}"
            gemini = getattr(http_request.app.state, "gemini_service", None)
            cache = getattr(http_request.app.state, "intelligence_cache", None)
            local_messages = getattr(http_request.app.state, "local_conversation_messages", None)

            if gemini is not None and isinstance(cache, dict):
                if local_messages is None or not isinstance(local_messages, dict):
                    http_request.app.state.local_conversation_messages = {}
                    local_messages = http_request.app.state.local_conversation_messages

                def _append_message() -> str:
                    history = local_messages.get(cache_key, [])
                    history.append({"sender": payload.sender, "message": payload.message})
                    local_messages[cache_key] = history
                    return "\n".join(f"{m['sender']}: {m['message']}" for m in history)

                async def _compute_and_publish() -> None:
                    try:
                        conversation_text = _append_message()
                        
                        logger.debug(f"    → Analyzing sentiment...")
                        sentiment = await gemini.analyze_sentiment(conversation_id, tenant_id, payload.message)
                        logger.debug(f"    ✓ Sentiment: {sentiment.sentiment.value} (confidence: {sentiment.confidence})")
                        
                        logger.debug(f"    → Detecting PII...")
                        pii = await gemini.detect_pii(conversation_id, tenant_id, payload.message)
                        logger.debug(f"    ✓ PII detected: {pii.has_pii} (entities: {len(pii.entities)})")
                        
                        logger.debug(f"    → Extracting insights...")
                        insights, summary = await gemini.extract_insights(conversation_id, tenant_id, conversation_text)
                        logger.debug(f"    ✓ Intent: {insights.intent.value}, Urgency: {insights.urgency.value}")
                        logger.debug(f"    ✓ Summary: {summary.tldr[:60]}...")

                        intelligence = AggregatedIntelligence(
                            conversation_id=conversation_id,
                            tenant_id=tenant_id,
                            sentiment=sentiment,
                            pii=pii,
                            insights=insights,
                            summary=summary,
                        )

                        cache[cache_key] = intelligence
                        logger.debug(f"    → Broadcasting intelligence to WebSocket clients...")
                        await broadcast_intelligence(conversation_id, intelligence)
                        logger.debug(f"    ✓ Broadcast complete")
                    except Exception as e:
                        logger.error(f"Dev intelligence compute failed: {e}", exc_info=True)

                # Fire and forget - don't block the response
                asyncio.create_task(_compute_and_publish())

        logger.debug(f"✓ Message {message_id} ingested successfully")
        logger.info(
            f"Message ingested: {message_id}",
            extra={
                "message_id": str(message_id),
                "conversation_id": payload.conversation_id,
                "tenant_id": tenant_id,
            },
        )

        return CreateMessageResponse(
            message_id=message_id,
            conversation_id=payload.conversation_id,
            status="accepted",
            timestamp=support_message.timestamp,
        )

    except Exception as e:
        logger.error(f"Error ingesting message: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest message: {str(e)}",
        )
