"""Example script demonstrating SignalStream AI API usage."""

import asyncio
import json
import requests
import websockets
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"
WS_BASE_URL = "ws://localhost:8000"
CONVERSATION_ID = f"demo-conv-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
TENANT_ID = "demo-tenant"


def send_message(conversation_id: str, sender: str, message: str):
    """Send a message to the API.

    Args:
        conversation_id: Conversation identifier
        sender: Message sender (customer or agent)
        message: Message content

    Returns:
        Response from API
    """
    url = f"{API_BASE_URL}/v1/messages"

    payload = {
        "conversation_id": conversation_id,
        "sender": sender,
        "message": message,
        "channel": "chat",
        "tenant_id": TENANT_ID,
    }

    response = requests.post(url, json=payload)
    response.raise_for_status()

    print(f"✅ Message sent: {response.json()}")
    return response.json()


def get_insights(conversation_id: str):
    """Get conversation intelligence.

    Args:
        conversation_id: Conversation identifier

    Returns:
        Intelligence data
    """
    url = f"{API_BASE_URL}/v1/conversations/{conversation_id}/insights"
    params = {"tenant_id": TENANT_ID}

    response = requests.get(url, params=params)
    response.raise_for_status()

    intelligence = response.json()
    print(f"\n📊 Intelligence retrieved:")
    print(json.dumps(intelligence, indent=2))
    return intelligence


async def stream_insights(conversation_id: str, duration: int = 30):
    """Stream real-time intelligence updates.

    Args:
        conversation_id: Conversation identifier
        duration: How long to listen (seconds)
    """
    url = f"{WS_BASE_URL}/ws/conversations/{conversation_id}/stream"

    print(f"\n🔄 Connecting to WebSocket: {url}")

    try:
        async with websockets.connect(url) as websocket:
            print("✅ WebSocket connected!")

            # Send ping to keep alive
            await websocket.send("ping")

            # Listen for updates
            end_time = asyncio.get_event_loop().time() + duration

            while asyncio.get_event_loop().time() < end_time:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    data = json.loads(message)

                    print(f"\n📨 Received update: {data.get('type')}")

                    if data.get("type") == "intelligence_update":
                        print("   Intelligence update:")
                        intel_data = data.get("data", {})
                        if intel_data.get("sentiment"):
                            print(
                                f"   - Sentiment: {intel_data['sentiment'].get('sentiment')}"
                            )
                        if intel_data.get("insights"):
                            print(f"   - Intent: {intel_data['insights'].get('intent')}")
                            print(
                                f"   - Urgency: {intel_data['insights'].get('urgency')}"
                            )

                except asyncio.TimeoutError:
                    # Send ping to keep connection alive
                    await websocket.send("ping")
                    continue

            print("\n✅ WebSocket session complete")

    except Exception as e:
        print(f"\n❌ WebSocket error: {e}")


def main():
    """Run the example demo."""
    print("=" * 70)
    print("🚀 SignalStream AI - Demo Script")
    print("=" * 70)
    print(f"Conversation ID: {CONVERSATION_ID}")
    print(f"Tenant ID: {TENANT_ID}")
    print("=" * 70)

    # Test 1: Send customer message
    print("\n1️⃣ Sending customer message...")
    send_message(
        CONVERSATION_ID,
        "customer",
        "I'm very frustrated! My order #12345 arrived damaged and I need a refund immediately!",
    )

    # Wait for processing
    print("\n⏳ Waiting for AI processing (5 seconds)...")
    import time

    time.sleep(5)

    # Test 2: Get insights
    print("\n2️⃣ Retrieving conversation insights...")
    try:
        get_insights(CONVERSATION_ID)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print("⚠️  Intelligence not yet available (still processing)")
        else:
            raise

    # Test 3: Send agent response
    print("\n3️⃣ Sending agent response...")
    send_message(
        CONVERSATION_ID,
        "agent",
        "I sincerely apologize for the damaged order. I'm processing your refund right now. You should see the credit in 3-5 business days.",
    )

    # Test 4: Stream real-time updates
    print("\n4️⃣ Streaming real-time intelligence updates...")
    print("   (Listening for 30 seconds...)")

    try:
        asyncio.run(stream_insights(CONVERSATION_ID, duration=30))
    except KeyboardInterrupt:
        print("\n⏹️  Streaming interrupted")

    # Test 5: Final insights
    print("\n5️⃣ Final intelligence check...")
    time.sleep(3)
    try:
        get_insights(CONVERSATION_ID)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print("⚠️  Intelligence not yet available")
        else:
            raise

    print("\n" + "=" * 70)
    print("✅ Demo complete!")
    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
