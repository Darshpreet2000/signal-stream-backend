"""Mock intelligence with progressive updates - simulates real AI agent timing."""

from datetime import datetime, timedelta
from typing import Dict, Any, List
import asyncio


class MockIntelligenceService:
    """Service that provides progressive mock intelligence updates."""

    def __init__(self):
        """Initialize per-conversation message counters and state cache."""
        self.conversation_counters = {}
        self.conversation_state = {}

    async def get_progressive_updates(
        self, conversation_id: str, tenant_id: str, message_text: str, sender: str,
        broadcast_callback
    ) -> None:
        """Generate and broadcast progressive intelligence updates.
        
        Simulates real AI agents completing at different times:
        - Message 1 (Customer): 1 update
        - Message 2 (Agent): 3 updates  
        - Message 3 (Customer): 4 updates
        - Message 4 (Agent): 3 updates
        - Message 5 (Customer): 4 updates
        
        Args:
            conversation_id: Conversation ID
            tenant_id: Tenant ID
            message_text: The message text
            sender: Message sender (customer/agent)
            broadcast_callback: Async function to broadcast each update
        """
        # Track per-conversation message count
        cache_key = f"{tenant_id}:{conversation_id}"
        if cache_key not in self.conversation_counters:
            self.conversation_counters[cache_key] = 0
            self.conversation_state[cache_key] = {}
        
        self.conversation_counters[cache_key] += 1
        msg_num = self.conversation_counters[cache_key]
        
        # Get current state
        current_state = self.conversation_state[cache_key]
        
        # Generate progressive updates based on message number
        if msg_num == 1:
            # Message 1: Single complete update
            state = self._get_message_1_state(conversation_id, tenant_id, message_text)
            self.conversation_state[cache_key] = state
            await broadcast_callback(state)
            
        elif msg_num == 2:
            # Message 2 (Agent): 3 progressive updates
            # Update 1: PII changes
            await asyncio.sleep(0.1)
            current_state["pii"]["redacted_text"] = message_text
            current_state["pii"]["timestamp"] = datetime.utcnow().isoformat()
            current_state["last_updated"] = datetime.utcnow().isoformat()
            await broadcast_callback(dict(current_state))
            
            # Update 2: Insights changes
            await asyncio.sleep(0.1)
            current_state["insights"]["timestamp"] = datetime.utcnow().isoformat()
            current_state["last_updated"] = datetime.utcnow().isoformat()
            await broadcast_callback(dict(current_state))
            
            # Update 3: Summary changes
            await asyncio.sleep(0.1)
            current_state["summary"]["agent_response"] = "Agent expresses empathy and commits to resolving the issue quickly."
            current_state["summary"]["timestamp"] = datetime.utcnow().isoformat()
            current_state["last_updated"] = datetime.utcnow().isoformat()
            await broadcast_callback(dict(current_state))
            
        elif msg_num == 3:
            # Message 3 (Customer): 4 progressive updates - PII DETECTED!
            # Update 1: Sentiment changes
            await asyncio.sleep(0.1)
            current_state["sentiment"]["confidence"] = 0.9
            current_state["sentiment"]["reasoning"] = "The customer is still expressing frustration by stating they don't have time for back-and-forth, indicating continued stress about the account lockout and the need for immediate access to funds."
            current_state["sentiment"]["timestamp"] = datetime.utcnow().isoformat()
            current_state["last_updated"] = datetime.utcnow().isoformat()
            await broadcast_callback(dict(current_state))
            
            # Update 2: Summary changes (mentions Sarah, account 4421)
            await asyncio.sleep(1.9)
            current_state["summary"]["tldr"] = "Customer Sarah, account ending 4421, is locked out and needs immediate access to funds."
            current_state["summary"]["customer_issue"] = "Customer is locked out of their bank account and needs immediate access to funds."
            current_state["summary"]["agent_response"] = None
            current_state["summary"]["key_points"] = ["Customer is frustrated due to being locked out of their account.", "Customer has urgent financial obligations.", "Customer provided account details and phone number."]
            current_state["summary"]["timestamp"] = datetime.utcnow().isoformat()
            current_state["last_updated"] = datetime.utcnow().isoformat()
            await broadcast_callback(dict(current_state))
            
            # Update 3: PII DETECTION - Sarah, 4421, phone number
            await asyncio.sleep(0.4)
            current_state["pii"]["has_pii"] = True
            current_state["pii"]["entities"] = [
                {"type": "name", "value": "Sarah", "start_index": 10, "end_index": 15},
                {"type": "account_number", "value": "4421", "start_index": 29, "end_index": 33},
                {"type": "phone", "value": "9123443454", "start_index": 48, "end_index": 58}
            ]
            current_state["pii"]["redacted_text"] = "My name is [REDACTED], account ending [REDACTED], and phone is [REDACTED] . I don't have time for back-and-forth."
            current_state["pii"]["timestamp"] = datetime.utcnow().isoformat()
            current_state["last_updated"] = datetime.utcnow().isoformat()
            await broadcast_callback(dict(current_state))
            
            # Update 4: Insights changes (escalation + time sensitivity)
            await asyncio.sleep(0.3)
            current_state["insights"]["suggested_actions"] = ["Offer apology and acknowledge frustration", "Provide immediate resolution", "Escalate to senior support"]
            current_state["insights"]["requires_escalation"] = True
            current_state["insights"]["key_concerns"] = ["Account lockout", "Inability to pay bills", "Time sensitivity"]
            current_state["insights"]["timestamp"] = datetime.utcnow().isoformat()
            current_state["last_updated"] = datetime.utcnow().isoformat()
            await broadcast_callback(dict(current_state))
            
        elif msg_num == 4:
            # Message 4 (Agent): 3 progressive updates - RESOLUTION MESSAGE
            # Update 1: Summary changes (account resolved)
            await asyncio.sleep(0.1)
            current_state["summary"]["tldr"] = "Customer Sarah, account ending 4421, is now able to access her account after the agent resolved the lockout."
            current_state["summary"]["customer_issue"] = "Customer is locked out of their bank account and needs immediate access to funds."
            current_state["summary"]["agent_response"] = "Agent has removed the account restriction, reset online access, and extended the bill-pay grace period."
            current_state["summary"]["key_points"] = ["Customer is frustrated due to being locked out of their account.", "Customer has urgent financial obligations."]
            current_state["summary"]["next_steps"] = ["Confirm customer can log in successfully.", "Monitor account activity."]
            current_state["summary"]["timestamp"] = datetime.utcnow().isoformat()
            current_state["last_updated"] = datetime.utcnow().isoformat()
            await broadcast_callback(dict(current_state))
            
            # Update 2: PII changes (agent message)
            await asyncio.sleep(2.9)
            current_state["pii"]["redacted_text"] = message_text
            current_state["pii"]["timestamp"] = datetime.utcnow().isoformat()
            current_state["last_updated"] = datetime.utcnow().isoformat()
            await broadcast_callback(dict(current_state))
            
            # Update 3: Insights changes (Technical Support, no escalation)
            await asyncio.sleep(0.2)
            current_state["insights"]["categories"] = ["Account Access", "Technical Support"]
            current_state["insights"]["suggested_actions"] = ["Apologize and acknowledge frustration", "Provide immediate resolution"]
            current_state["insights"]["requires_escalation"] = False
            current_state["insights"]["key_concerns"] = ["Account lockout", "Inability to pay bills"]
            current_state["insights"]["timestamp"] = datetime.utcnow().isoformat()
            current_state["last_updated"] = datetime.utcnow().isoformat()
            await broadcast_callback(dict(current_state))
            
        elif msg_num == 5:
            # Message 5 (Customer): 4 progressive updates - SENTIMENT CHANGE TO POSITIVE
            # Update 1: PII changes
            await asyncio.sleep(0.3)
            current_state["pii"]["redacted_text"] = message_text
            current_state["pii"]["timestamp"] = datetime.utcnow().isoformat()
            current_state["last_updated"] = datetime.utcnow().isoformat()
            await broadcast_callback(dict(current_state))
            
            # Update 2: Sentiment changes to POSITIVE
            await asyncio.sleep(4.7)
            current_state["sentiment"]["sentiment"] = "positive"
            current_state["sentiment"]["confidence"] = 0.95
            current_state["sentiment"]["emotion"] = "satisfied"
            current_state["sentiment"]["reasoning"] = "The customer expresses relief and uses the phrase 'huge relief' indicating a significant positive shift from the initial frustration. The customer also says 'thanks'."
            current_state["sentiment"]["timestamp"] = datetime.utcnow().isoformat()
            current_state["last_updated"] = datetime.utcnow().isoformat()
            await broadcast_callback(dict(current_state))
            
            # Update 3: Summary changes (regained access)
            await asyncio.sleep(0.4)
            current_state["summary"]["tldr"] = "Customer Sarah has regained access to her account ending 4421 and confirmed successful login."
            current_state["summary"]["customer_issue"] = "Customer was locked out of their bank account and needed immediate access to funds."
            current_state["summary"]["agent_response"] = "Agent has removed the account restriction, reset online access, and extended the bill-pay grace period."
            current_state["summary"]["key_points"] = ["Customer was frustrated due to being locked out.", "Customer had urgent financial obligations.", "Customer provided account details and phone number.", "Agent resolved the issue.", "Customer confirmed successful login."]
            current_state["summary"]["next_steps"] = ["Monitor account activity."]
            current_state["summary"]["timestamp"] = datetime.utcnow().isoformat()
            current_state["last_updated"] = datetime.utcnow().isoformat()
            await broadcast_callback(dict(current_state))
            
            # Update 4: Insights changes (urgency Critical → High)
            await asyncio.sleep(0.3)
            current_state["insights"]["categories"] = ["Account Access", "Technical Issue"]
            current_state["insights"]["urgency"] = "High"
            current_state["insights"]["suggested_actions"] = ["Confirm resolution", "Monitor account activity"]
            current_state["insights"]["requires_escalation"] = False
            current_state["insights"]["key_concerns"] = ["Account lockout resolved", "Customer satisfaction confirmed"]
            current_state["insights"]["timestamp"] = datetime.utcnow().isoformat()
            current_state["last_updated"] = datetime.utcnow().isoformat()
            await broadcast_callback(dict(current_state))
        
        else:
            # Default: single update
            await broadcast_callback(dict(current_state))
    
    def _get_message_1_state(self, conversation_id: str, tenant_id: str, message_text: str) -> Dict[str, Any]:
        """Get initial complete state for message 1."""
        timestamp = datetime.utcnow().isoformat()
        return {
            "conversation_id": conversation_id,
            "tenant_id": tenant_id,
            "sentiment": {
                "conversation_id": conversation_id,
                "tenant_id": tenant_id,
                "sentiment": "negative",
                "confidence": 0.95,
                "emotion": "frustrated",
                "reasoning": "The customer expresses frustration and urgency due to being locked out of their account and having bills due. The language used ('frustrating', 'need this fixed right now') indicates a negative emotional state.",
                "timestamp": timestamp
            },
            "pii": {
                "conversation_id": conversation_id,
                "tenant_id": tenant_id,
                "has_pii": False,
                "entities": [],
                "redacted_text": message_text,
                "timestamp": timestamp
            },
            "insights": {
                "conversation_id": conversation_id,
                "tenant_id": tenant_id,
                "intent": "Account Issue",
                "urgency": "Critical",
                "categories": ["Account Access", "Financial"],
                "suggested_actions": ["Offer apology and acknowledge frustration", "Provide immediate resolution", "Escalate to senior support", "Offer credit for inconvenience"],
                "requires_escalation": True,
                "estimated_resolution_time": "< 1 hour",
                "key_concerns": ["Account lockout", "Inability to pay bills", "Financial urgency"],
                "timestamp": timestamp
            },
            "summary": {
                "conversation_id": conversation_id,
                "tenant_id": tenant_id,
                "tldr": "Customer is locked out of their bank account and needs immediate access to funds to pay bills.",
                "customer_issue": "Customer is locked out of their bank account and cannot access funds to pay bills due today.",
                "agent_response": None,
                "key_points": ["Customer is frustrated due to being locked out of their account.", "Customer has urgent financial obligations."],
                "next_steps": ["Agent to investigate the reason for the account lockout.", "Agent to provide immediate assistance to restore account access."],
                "timestamp": timestamp
            },
            "last_updated": timestamp
        }
