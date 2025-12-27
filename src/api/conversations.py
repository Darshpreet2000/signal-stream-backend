"""Conversations API - Consumer endpoints for retrieving intelligence."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status

from ..config import Settings, get_settings
from ..models import AggregatedIntelligence

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversations", tags=["conversations"])


def get_intelligence_cache(request: Request) -> dict:
    """Dependency to get intelligence cache."""
    cache = getattr(request.app.state, "intelligence_cache", None)
    if cache is None:
        return {}
    return cache


@router.get(
    "/{conversation_id}/insights",
    response_model=AggregatedIntelligence,
    summary="Get Conversation Intelligence",
    description="Retrieve the latest AI-generated intelligence for a conversation.",
)
async def get_conversation_insights(
    conversation_id: str,
    tenant_id: Optional[str] = None,
    cache: dict = Depends(get_intelligence_cache),
    settings: Settings = Depends(get_settings),
) -> AggregatedIntelligence:
    """Get aggregated intelligence for a conversation.

    This endpoint provides real-time access to all AI agent outputs:
    - Sentiment analysis
    - PII detection
    - Intent and insights
    - Conversation summary

    Args:
        conversation_id: Unique conversation identifier
        tenant_id: Optional tenant ID (defaults to demo tenant)
        cache: Intelligence cache
        settings: Application settings

    Returns:
        Aggregated intelligence for the conversation

    Raises:
        404: Conversation not found or not yet processed
    """
    # Determine tenant ID
    if not tenant_id:
        tenant_id = settings.default_tenant_id

    # Look up in cache
    cache_key = f"{tenant_id}:{conversation_id}"

    if cache_key not in cache:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found or not yet processed",
        )

    intelligence = cache[cache_key]

    logger.info(
        f"Intelligence retrieved for {conversation_id}",
        extra={"conversation_id": conversation_id, "tenant_id": tenant_id},
    )

    return intelligence
