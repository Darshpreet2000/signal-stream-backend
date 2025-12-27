#!/usr/bin/env python
"""
Comprehensive API Test Script for SignalStream AI Backend
Tests all endpoints with dummy data in a realistic workflow.
"""

import asyncio
import json
import time
from datetime import datetime
from typing import List, Dict, Any
import aiohttp
import websockets


# Configuration
BASE_URL = "http://localhost:8000"
API_VERSION = "v1"
TENANT_ID = "demo-tenant"


class Colors:
    """Terminal colors for pretty output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}")
    print(f"{text:^70}")
    print(f"{'='*70}{Colors.ENDC}\n")


def print_success(text: str):
    """Print success message."""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_error(text: str):
    """Print error message."""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_info(text: str):
    """Print info message."""
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")


def print_warning(text: str):
    """Print warning message."""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


# Dummy Conversation Data
DUMMY_MESSAGES = [
    {
        "conversation_id": "conv-001",
        "content": "Hi, I've been having issues with my account. I can't log in anymore and I'm really frustrated!",
        "sender": "customer",
        "metadata": {
            "channel": "chat",
            "customer_email": "john.doe@example.com",
            "customer_name": "John Doe"
        }
    },
    {
        "conversation_id": "conv-001",
        "content": "Hello John! I understand your frustration. Let me help you with that login issue. Can you tell me what error message you're seeing?",
        "sender": "agent",
        "metadata": {
            "agent_id": "agent-123",
            "agent_name": "Sarah"
        }
    },
    {
        "conversation_id": "conv-001",
        "content": "It says 'Invalid credentials' but I'm sure my password is correct. This is really annoying!",
        "sender": "customer",
        "metadata": {
            "channel": "chat",
            "customer_email": "john.doe@example.com"
        }
    },
    {
        "conversation_id": "conv-001",
        "content": "I see. Let me check your account. Can you confirm your email address is john.doe@example.com?",
        "sender": "agent",
        "metadata": {
            "agent_id": "agent-123"
        }
    },
    {
        "conversation_id": "conv-001",
        "content": "Yes, that's correct. My SSN is 123-45-6789 and my phone is 555-123-4567 if you need verification.",
        "sender": "customer",
        "metadata": {
            "channel": "chat"
        }
    },
    {
        "conversation_id": "conv-001",
        "content": "Perfect! I found the issue. Your account was temporarily locked due to multiple failed login attempts. I've unlocked it for you. Please try logging in again with your password.",
        "sender": "agent",
        "metadata": {
            "agent_id": "agent-123"
        }
    },
    {
        "conversation_id": "conv-001",
        "content": "Great! It works now. Thank you so much for your help!",
        "sender": "customer",
        "metadata": {
            "channel": "chat"
        }
    },
]


async def check_health() -> bool:
    """Check if the API is healthy and ready."""
    print_header("HEALTH CHECK")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/health") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print_success(f"API is healthy: {json.dumps(data, indent=2)}")
                    return True
                else:
                    print_error(f"Health check failed with status {resp.status}")
                    return False
    except Exception as e:
        print_error(f"Health check failed: {e}")
        return False


async def send_message(session: aiohttp.ClientSession, message: Dict[str, Any]) -> bool:
    """Send a single message to the API."""
    try:
        payload = {
            "conversation_id": message["conversation_id"],
            "content": message["content"],
            "sender": message["sender"],
            "tenant_id": TENANT_ID,
            "metadata": message.get("metadata", {})
        }
        
        async with session.post(
            f"{BASE_URL}/{API_VERSION}/messages",
            json=payload,
            headers={"Content-Type": "application/json"}
        ) as resp:
            if resp.status == 202:
                data = await resp.json()
                print_success(f"Message sent: {message['sender'][:20]}... (ID: {data.get('message_id', 'N/A')[:8]}...)")
                return True
            else:
                error_text = await resp.text()
                print_error(f"Failed to send message (Status {resp.status}): {error_text[:100]}")
                return False
    except Exception as e:
        print_error(f"Error sending message: {e}")
        return False


async def test_message_ingestion():
    """Test the message ingestion endpoint."""
    print_header("TEST 1: MESSAGE INGESTION API")
    print_info("Sending conversation messages with dummy data...")
    
    async with aiohttp.ClientSession() as session:
        success_count = 0
        for i, message in enumerate(DUMMY_MESSAGES, 1):
            print(f"\n{Colors.BOLD}Message {i}/{len(DUMMY_MESSAGES)}:{Colors.ENDC}")
            print(f"  Sender: {message['sender']}")
            print(f"  Content: {message['content'][:60]}...")
            
            if await send_message(session, message):
                success_count += 1
            
            # Small delay between messages to simulate real conversation
            await asyncio.sleep(1)
        
        print(f"\n{Colors.BOLD}Summary:{Colors.ENDC}")
        print_success(f"Successfully sent {success_count}/{len(DUMMY_MESSAGES)} messages")
        
        if success_count == len(DUMMY_MESSAGES):
            print_info("Waiting 15 seconds for AI agents to process the conversation...")
            await asyncio.sleep(15)
            return True
        else:
            print_warning("Some messages failed to send")
            return False


async def test_conversation_insights():
    """Test the conversation insights endpoint."""
    print_header("TEST 2: CONVERSATION INSIGHTS API")
    print_info("Fetching AI-generated insights for the conversation...")
    
    conversation_id = DUMMY_MESSAGES[0]["conversation_id"]
    max_attempts = 10
    attempt = 0
    
    async with aiohttp.ClientSession() as session:
        while attempt < max_attempts:
            attempt += 1
            print(f"\nAttempt {attempt}/{max_attempts}:")
            
            try:
                async with session.get(
                    f"{BASE_URL}/{API_VERSION}/conversations/{conversation_id}/insights",
                    params={"tenant_id": TENANT_ID}
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        
                        if data.get("status") == "completed":
                            print_success("Intelligence is ready!")
                            print(f"\n{Colors.BOLD}Conversation Intelligence:{Colors.ENDC}")
                            print(json.dumps(data, indent=2))
                            
                            # Validate all AI components are present
                            intelligence = data.get("intelligence", {})
                            components = ["sentiment", "pii_detected", "insights", "summary"]
                            missing = [c for c in components if c not in intelligence]
                            
                            if missing:
                                print_warning(f"Missing components: {', '.join(missing)}")
                            else:
                                print_success("All AI components are present!")
                            
                            return True
                        
                        elif data.get("status") == "processing":
                            print_info("Intelligence is still processing...")
                            print(f"  Available components: {', '.join(data.get('intelligence', {}).keys())}")
                        
                        else:
                            print_warning(f"Status: {data.get('status')}")
                    
                    elif resp.status == 404:
                        print_warning("Conversation not found yet")
                    
                    else:
                        error_text = await resp.text()
                        print_error(f"Request failed (Status {resp.status}): {error_text[:100]}")
                
            except Exception as e:
                print_error(f"Error fetching insights: {e}")
            
            if attempt < max_attempts:
                print_info("Waiting 3 seconds before next attempt...")
                await asyncio.sleep(3)
        
        print_error(f"Intelligence not ready after {max_attempts} attempts")
        return False


async def test_websocket_streaming():
    """Test the WebSocket streaming endpoint."""
    print_header("TEST 3: WEBSOCKET STREAMING")
    print_info("Testing real-time intelligence streaming...")
    
    conversation_id = DUMMY_MESSAGES[0]["conversation_id"]
    ws_url = f"ws://localhost:8000/ws/conversations/{conversation_id}/stream?tenant_id={TENANT_ID}"
    
    try:
        print(f"Connecting to: {ws_url}")
        async with websockets.connect(ws_url) as websocket:
            print_success("WebSocket connection established")
            
            # Wait for initial message or updates
            try:
                messages_received = 0
                timeout = 10  # 10 seconds timeout
                
                while messages_received < 3:  # Try to receive a few messages
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=timeout)
                        messages_received += 1
                        
                        try:
                            data = json.loads(message)
                            print_success(f"Received update {messages_received}:")
                            print(f"  Event: {data.get('event', 'N/A')}")
                            print(f"  Status: {data.get('status', 'N/A')}")
                            if 'intelligence' in data:
                                print(f"  Components: {', '.join(data['intelligence'].keys())}")
                        except json.JSONDecodeError:
                            print_warning(f"Received non-JSON message: {message[:100]}")
                    
                    except asyncio.TimeoutError:
                        print_info(f"No more messages after {timeout}s timeout")
                        break
                
                if messages_received > 0:
                    print_success(f"Successfully received {messages_received} WebSocket messages")
                    return True
                else:
                    print_warning("No messages received on WebSocket")
                    return False
                
            except Exception as e:
                print_error(f"Error receiving WebSocket messages: {e}")
                return False
    
    except Exception as e:
        print_error(f"WebSocket connection failed: {e}")
        print_warning("This might be expected if the conversation hasn't been processed yet")
        return False


async def run_comprehensive_test():
    """Run all tests in sequence."""
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("╔═══════════════════════════════════════════════════════════════════╗")
    print("║        SignalStream AI Backend - Comprehensive API Tests         ║")
    print("╚═══════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}")
    
    print_info(f"Testing against: {BASE_URL}")
    print_info(f"Tenant ID: {TENANT_ID}")
    print_info(f"Test Conversation ID: {DUMMY_MESSAGES[0]['conversation_id']}")
    print_info(f"Timestamp: {datetime.now().isoformat()}")
    
    # Step 1: Health Check
    if not await check_health():
        print_error("\n⚠️  API is not healthy. Please start the backend server first.")
        print_info("Run: python run.py")
        return
    
    # Step 2: Message Ingestion
    if not await test_message_ingestion():
        print_error("\n⚠️  Message ingestion test failed")
        return
    
    # Step 3: Conversation Insights
    insights_success = await test_conversation_insights()
    
    # Step 4: WebSocket Streaming
    websocket_success = await test_websocket_streaming()
    
    # Final Summary
    print_header("TEST SUMMARY")
    
    results = [
        ("Health Check", True),
        ("Message Ingestion", True),
        ("Conversation Insights", insights_success),
        ("WebSocket Streaming", websocket_success),
    ]
    
    print(f"{Colors.BOLD}Test Results:{Colors.ENDC}")
    for test_name, success in results:
        status = f"{Colors.OKGREEN}✓ PASSED{Colors.ENDC}" if success else f"{Colors.FAIL}✗ FAILED{Colors.ENDC}"
        print(f"  {test_name:.<50} {status}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"\n{Colors.BOLD}Overall: {passed}/{total} tests passed{Colors.ENDC}")
    
    if passed == total:
        print_success("\n🎉 All tests passed! Your SignalStream AI backend is working correctly!")
    else:
        print_warning("\n⚠️  Some tests failed. Check the logs above for details.")
    
    print_info("\nNext steps:")
    print("  1. Check backend logs for any errors")
    print("  2. Verify Kafka topics have messages")
    print("  3. Check Gemini API quota and connectivity")


if __name__ == "__main__":
    try:
        asyncio.run(run_comprehensive_test())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}Test interrupted by user{Colors.ENDC}")
    except Exception as e:
        print(f"\n\n{Colors.FAIL}Unexpected error: {e}{Colors.ENDC}")
