"""WebSocket API for real-time intelligence streaming."""

import asyncio
import json
import logging
from typing import Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends

from ..config import Settings, get_settings
from ..models import AggregatedIntelligence

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])

# Global connection manager
class ConnectionManager:
    """Manages WebSocket connections."""

    def __init__(self):
        """Initialize connection manager."""
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, conversation_id: str):
        """Connect a client to a conversation stream.

        Args:
            websocket: WebSocket connection
            conversation_id: Conversation ID to subscribe to
        """
        await websocket.accept()

        if conversation_id not in self.active_connections:
            self.active_connections[conversation_id] = set()

        self.active_connections[conversation_id].add(websocket)

        logger.info(
            f"Client connected to conversation {conversation_id}",
            extra={
                "conversation_id": conversation_id,
                "total_connections": len(self.active_connections[conversation_id]),
            },
        )

    def disconnect(self, websocket: WebSocket, conversation_id: str):
        """Disconnect a client from a conversation stream.

        Args:
            websocket: WebSocket connection
            conversation_id: Conversation ID
        """
        if conversation_id in self.active_connections:
            self.active_connections[conversation_id].discard(websocket)

            if not self.active_connections[conversation_id]:
                del self.active_connections[conversation_id]

        logger.info(
            f"Client disconnected from conversation {conversation_id}",
            extra={"conversation_id": conversation_id},
        )

    async def broadcast(self, conversation_id: str, message: dict):
        """Broadcast message to all clients subscribed to a conversation.

        Args:
            conversation_id: Conversation ID
            message: Message to broadcast
        """
        if conversation_id not in self.active_connections:
            logger.debug(f"→ [broadcast] conv_id={conversation_id}: No active connections")
            return

        client_count = len(self.active_connections[conversation_id])
        logger.debug(f"→ [broadcast] conv_id={conversation_id}, clients={client_count}")
        disconnected = set()

        sent_count = 0
        for websocket in self.active_connections[conversation_id]:
            try:
                await websocket.send_json(message)
                sent_count += 1
                logger.debug(f"  ✓ Sent to client {sent_count}")
            except Exception as e:
                logger.error(f"  ✗ Error broadcasting to client: {e}")
                disconnected.add(websocket)

        # Clean up disconnected clients
        for websocket in disconnected:
            self.disconnect(websocket, conversation_id)
        
        logger.debug(f"  ✓ Broadcast complete: sent={sent_count}, disconnected={len(disconnected)}")


# Global manager instance
manager = ConnectionManager()


@router.websocket("/ws/conversations/{conversation_id}/stream")
async def websocket_conversation_stream(
    websocket: WebSocket,
    conversation_id: str,
    settings: Settings = Depends(get_settings),
):
    """WebSocket endpoint for real-time intelligence streaming.

    Clients connect to this endpoint to receive real-time updates
    as AI agents process conversations.

    Args:
        websocket: WebSocket connection
        conversation_id: Conversation ID to stream
        settings: Application settings
    """
    await manager.connect(websocket, conversation_id)

    try:
        # Send initial connection message
        await websocket.send_json(
            {
                "type": "connected",
                "conversation_id": conversation_id,
                "message": "Connected to conversation stream",
            }
        )

        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Receive any messages from client (e.g., ping/pong)
                data = await websocket.receive_text()

                # Echo back (or handle specific commands)
                if data == "ping":
                    await websocket.send_json({"type": "pong"})

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break

    finally:
        manager.disconnect(websocket, conversation_id)


# Function to broadcast intelligence updates (called by aggregation consumer)
async def broadcast_intelligence(
    conversation_id: str, intelligence: AggregatedIntelligence
):
    """Broadcast intelligence update to WebSocket clients.

    This function is called by the aggregation consumer when new
    intelligence is available.

    Args:
        conversation_id: Conversation ID
        intelligence: Aggregated intelligence
    """
    message = {
        "type": "intelligence_update",
        "conversation_id": conversation_id,
        "data": json.loads(intelligence.model_dump_json()),
    }

    await manager.broadcast(conversation_id, message)
