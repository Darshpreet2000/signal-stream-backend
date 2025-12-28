"""Mock intelligence data for testing purposes - returns exact hardcoded responses."""

from datetime import datetime
from typing import Dict, Any


class MockIntelligenceService:
    """Service that provides hardcoded mock intelligence data matching demo flow exactly."""

    def __init__(self):
        """Initialize per-conversation message counters."""
        self.conversation_counters = {}

    def get_mock_intelligence(
        self, conversation_id: str, tenant_id: str, message_text: str, sender: str
    ) -> Dict[str, Any]:
        """Get hardcoded mock intelligence data matching exact demo flow.
        
        Returns exactly the same intelligence updates as shown in the demo,
        progressing through 14 different states based on message number.
        
        Args:
            conversation_id: Conversation ID
            tenant_id: Tenant ID  
            message_text: The message text (used for redacted_text in later messages)
            sender: Message sender (customer/agent)
            
        Returns:
            Hardcoded mock intelligence data for the specific message number
        """
        # Track per-conversation message count
        if conversation_id not in self.conversation_counters:
            self.conversation_counters[conversation_id] = 0
        
        self.conversation_counters[conversation_id] += 1
        msg_num = self.conversation_counters[conversation_id]
        
        now = datetime.utcnow().isoformat()
        
        # Hardcoded responses matching the exact demo flow
        if msg_num <= 14:
            return self._get_hardcoded_response(msg_num, conversation_id, tenant_id, message_text, now)
        else:
            # Beyond message 14, keep returning the final resolved state
            return self._get_hardcoded_response(14, conversation_id, tenant_id, message_text, now)
    
    def _get_hardcoded_response(self, msg_num: int, conversation_id: str, tenant_id: str, 
                                message_text: str, timestamp: str) -> Dict[str, Any]:
        """Get hardcoded response for specific message number."""
        
        # Messages 1-5: Initial frustration, no PII
        if msg_num == 1:
            return {
                "conversation_id": conversation_id,
                "tenant_id": tenant_id,
                "sentiment": {
                    "conversation_id": conversation_id,
                    "tenant_id": tenant_id,
                    "sentiment": "negative",
                    "confidence": 0.95,
                    "emotion": "frustrated",
                    "reasoning": "The customer expresses frustration and urgency due to being locked out of their account and having bills due. The language used, such as 'so frustrating' and 'I need this fixed right now,' indicates a negative emotional state.",
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
                    "suggested_actions": ["Apologize and acknowledge frustration", "Provide immediate resolution", "Offer credit for inconvenience"],
                    "requires_escalation": False,
                    "estimated_resolution_time": "< 1 hour",
                    "key_concerns": ["Locked out of account", "Unable to pay bills", "Frustration"],
                    "timestamp": timestamp
                },
                "summary": {
                    "conversation_id": conversation_id,
                    "tenant_id": tenant_id,
                    "tldr": "Customer is locked out of their bank account and needs immediate access to funds to pay bills.",
                    "customer_issue": "Customer is locked out of their bank account and cannot access funds to pay bills due today.",
                    "agent_response": None,
                    "key_points": ["Customer is frustrated and needs immediate assistance.", "Customer has bills due today."],
                    "next_steps": ["Agent to verify customer's identity.", "Agent to investigate the cause of the account lockout."],
                    "timestamp": timestamp
                },
                "last_updated": timestamp
            }
        
        elif msg_num == 2:
            return {
                "conversation_id": conversation_id,
                "tenant_id": tenant_id,
                "sentiment": {
                    "conversation_id": conversation_id,
                    "tenant_id": tenant_id,
                    "sentiment": "negative",
                    "confidence": 0.95,
                    "emotion": "frustrated",
                    "reasoning": "The customer expresses frustration and urgency due to being locked out of their account and having bills due. The language used, such as 'so frustrating' and 'I need this fixed right now,' indicates a negative emotional state.",
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
                    "suggested_actions": ["Apologize and acknowledge frustration", "Provide immediate resolution", "Offer credit for inconvenience"],
                    "requires_escalation": False,
                    "estimated_resolution_time": "< 1 hour",
                    "key_concerns": ["Locked out of account", "Unable to pay bills", "Frustration"],
                    "timestamp": timestamp
                },
                "summary": {
                    "conversation_id": conversation_id,
                    "tenant_id": tenant_id,
                    "tldr": "Customer is locked out of their bank account and needs immediate access to funds to pay bills.",
                    "customer_issue": "Customer is locked out of their bank account and cannot access funds to pay bills due today.",
                    "agent_response": "Agent expresses empathy and commits to resolving the issue quickly.",
                    "key_points": ["Customer is frustrated and needs immediate assistance.", "Customer has bills due today."],
                    "next_steps": ["Agent to verify customer's identity.", "Agent to investigate the cause of the account lockout."],
                    "timestamp": timestamp
                },
                "last_updated": timestamp
            }
        
        elif msg_num == 3:
            return {
                "conversation_id": conversation_id,
                "tenant_id": tenant_id,
                "sentiment": {
                    "conversation_id": conversation_id,
                    "tenant_id": tenant_id,
                    "sentiment": "negative",
                    "confidence": 0.95,
                    "emotion": "frustrated",
                    "reasoning": "The customer expresses frustration and urgency due to being locked out of their account and having bills due. The language used, such as 'so frustrating' and 'I need this fixed right now,' indicates a negative emotional state.",
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
                    "suggested_actions": ["Apologize and acknowledge frustration", "Provide immediate resolution", "Escalate to senior support", "Offer credit"],
                    "requires_escalation": True,
                    "estimated_resolution_time": "< 1 hour",
                    "key_concerns": ["Account lockout", "Inability to pay bills"],
                    "timestamp": timestamp
                },
                "summary": {
                    "conversation_id": conversation_id,
                    "tenant_id": tenant_id,
                    "tldr": "Customer is locked out of their bank account and needs immediate access to funds to pay bills.",
                    "customer_issue": "Customer is locked out of their bank account and cannot access funds to pay bills due today.",
                    "agent_response": "Agent expresses empathy and commits to resolving the issue quickly.",
                    "key_points": ["Customer is frustrated and needs immediate assistance.", "Customer has bills due today."],
                    "next_steps": ["Agent to verify customer's identity.", "Agent to investigate the cause of the account lockout."],
                    "timestamp": timestamp
                },
                "last_updated": timestamp
            }
        
        elif msg_num == 4:
            return {
                "conversation_id": conversation_id,
                "tenant_id": tenant_id,
                "sentiment": {
                    "conversation_id": conversation_id,
                    "tenant_id": tenant_id,
                    "sentiment": "negative",
                    "confidence": 0.95,
                    "emotion": "frustrated",
                    "reasoning": "The customer expresses frustration and urgency due to being locked out of their account and having bills due. The language used, such as 'so frustrating' and 'I need this fixed right now,' indicates a negative emotional state.",
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
                    "suggested_actions": ["Apologize and acknowledge frustration", "Provide immediate resolution", "Escalate to senior support", "Offer credit"],
                    "requires_escalation": True,
                    "estimated_resolution_time": "< 1 hour",
                    "key_concerns": ["Account lockout", "Inability to pay bills"],
                    "timestamp": timestamp
                },
                "summary": {
                    "conversation_id": conversation_id,
                    "tenant_id": tenant_id,
                    "tldr": "Customer is locked out of their bank account and needs immediate access to funds to pay bills.",
                    "customer_issue": "Customer is locked out of their bank account and cannot access funds to pay bills due today.",
                    "agent_response": None,
                    "key_points": ["Customer is frustrated and needs immediate assistance.", "Customer has bills due today.", "Customer provided account details and contact information."],
                    "next_steps": ["Agent to verify customer's identity.", "Agent to investigate the cause of the account lockout."],
                    "timestamp": timestamp
                },
                "last_updated": timestamp
            }
        
        elif msg_num == 5:
            return {
                "conversation_id": conversation_id,
                "tenant_id": tenant_id,
                "sentiment": {
                    "conversation_id": conversation_id,
                    "tenant_id": tenant_id,
                    "sentiment": "negative",
                    "confidence": 0.9,
                    "emotion": "frustrated",
                    "reasoning": "The customer is still expressing frustration. They are providing account details, indicating they are focused on getting the issue resolved quickly, but the underlying frustration from being locked out of their account remains evident. The lack of positive language suggests the negative sentiment persists.",
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
                    "suggested_actions": ["Apologize and acknowledge frustration", "Provide immediate resolution", "Escalate to senior support", "Offer credit"],
                    "requires_escalation": True,
                    "estimated_resolution_time": "< 1 hour",
                    "key_concerns": ["Account lockout", "Inability to pay bills"],
                    "timestamp": timestamp
                },
                "summary": {
                    "conversation_id": conversation_id,
                    "tenant_id": tenant_id,
                    "tldr": "Customer is locked out of their bank account and needs immediate access to funds to pay bills.",
                    "customer_issue": "Customer is locked out of their bank account and cannot access funds to pay bills due today.",
                    "agent_response": None,
                    "key_points": ["Customer is frustrated and needs immediate assistance.", "Customer has bills due today.", "Customer provided account details and contact information."],
                    "next_steps": ["Agent to verify customer's identity.", "Agent to investigate the cause of the account lockout."],
                    "timestamp": timestamp
                },
                "last_updated": timestamp
            }
        
        # Message 6: PII detected!
        elif msg_num == 6:
            return {
                "conversation_id": conversation_id,
                "tenant_id": tenant_id,
                "sentiment": {
                    "conversation_id": conversation_id,
                    "tenant_id": tenant_id,
                    "sentiment": "negative",
                    "confidence": 0.9,
                    "emotion": "frustrated",
                    "reasoning": "The customer is still expressing frustration. They are providing account details, indicating they are focused on getting the issue resolved quickly, but the underlying frustration from being locked out of their account remains evident. The lack of positive language suggests the negative sentiment persists.",
                    "timestamp": timestamp
                },
                "pii": {
                    "conversation_id": conversation_id,
                    "tenant_id": tenant_id,
                    "has_pii": True,
                    "entities": [
                        {"type": "name", "value": "Sarah Lee", "start_index": 10, "end_index": 19},
                        {"type": "account_number", "value": "4421", "start_index": 35, "end_index": 39},
                        {"type": "phone", "value": "24456455", "start_index": 58, "end_index": 66}
                    ],
                    "redacted_text": "My name is [REDACTED], account ending [REDACTED], and the phone number is [REDACTED]. I don't have time for back-and-forth.",
                    "timestamp": timestamp
                },
                "insights": {
                    "conversation_id": conversation_id,
                    "tenant_id": tenant_id,
                    "intent": "Account Issue",
                    "urgency": "Critical",
                    "categories": ["Account Access", "Financial"],
                    "suggested_actions": ["Apologize and acknowledge frustration", "Provide immediate resolution", "Escalate to senior support", "Offer credit"],
                    "requires_escalation": True,
                    "estimated_resolution_time": "< 1 hour",
                    "key_concerns": ["Account lockout", "Inability to pay bills"],
                    "timestamp": timestamp
                },
                "summary": {
                    "conversation_id": conversation_id,
                    "tenant_id": tenant_id,
                    "tldr": "Customer is locked out of their bank account and needs immediate access to funds to pay bills.",
                    "customer_issue": "Customer is locked out of their bank account and cannot access funds to pay bills due today.",
                    "agent_response": None,
                    "key_points": ["Customer is frustrated and needs immediate assistance.", "Customer has bills due today.", "Customer provided account details and contact information."],
                    "next_steps": ["Agent to verify customer's identity.", "Agent to investigate the cause of the account lockout."],
                    "timestamp": timestamp
                },
                "last_updated": timestamp
            }
        
        # Messages 7-11: PII persists, working on resolution
        elif msg_num in [7, 8, 9, 10, 11]:
            base_response = {
                "conversation_id": conversation_id,
                "tenant_id": tenant_id,
                "sentiment": {
                    "conversation_id": conversation_id,
                    "tenant_id": tenant_id,
                    "sentiment": "negative",
                    "confidence": 0.9,
                    "emotion": "frustrated",
                    "reasoning": "The customer is still expressing frustration. They are providing account details, indicating they are focused on getting the issue resolved quickly, but the underlying frustration from being locked out of their account remains evident. The lack of positive language suggests the negative sentiment persists.",
                    "timestamp": timestamp
                },
                "pii": {
                    "conversation_id": conversation_id,
                    "tenant_id": tenant_id,
                    "has_pii": True,
                    "entities": [
                        {"type": "name", "value": "Sarah Lee", "start_index": 10, "end_index": 19},
                        {"type": "account_number", "value": "4421", "start_index": 35, "end_index": 39},
                        {"type": "phone", "value": "24456455", "start_index": 58, "end_index": 66}
                    ],
                    "redacted_text": message_text,
                    "timestamp": timestamp
                },
                "insights": {
                    "conversation_id": conversation_id,
                    "tenant_id": tenant_id,
                    "intent": "Account Issue",
                    "urgency": "Critical",
                    "categories": ["Account Access", "Financial" if msg_num <= 8 else "Technical Support"],
                    "suggested_actions": ["Apologize and acknowledge frustration", "Provide immediate resolution"] + (["Escalate to senior support"] if msg_num == 7 else []),
                    "requires_escalation": True if msg_num == 7 else False,
                    "estimated_resolution_time": "< 1 hour",
                    "key_concerns": ["Locked out of account", "Inability to pay bills"],
                    "timestamp": timestamp
                },
                "summary": {
                    "conversation_id": conversation_id,
                    "tenant_id": tenant_id,
                    "tldr": "Customer's account lockout resolved; access restored, bill-pay grace period extended." if msg_num >= 9 else "Customer is locked out of their bank account and needs immediate access to funds to pay bills.",
                    "customer_issue": "Customer was locked out of their bank account." if msg_num >= 9 else "Customer is locked out of their bank account and cannot access funds to pay bills due today.",
                    "agent_response": "Account restriction removed, online access reset, and bill-pay grace period extended." if msg_num >= 9 else None,
                    "key_points": ["Customer's account lockout resolved.", "Customer can now access their account."] if msg_num >= 9 else ["Customer is frustrated and needs immediate assistance.", "Customer has bills due today.", "Customer provided account details and contact information."],
                    "next_steps": ["Customer to confirm account access.", "Monitor account activity."] if msg_num >= 9 else ["Agent to verify customer's identity.", "Agent to investigate the cause of the account lockout."],
                    "timestamp": timestamp
                },
                "last_updated": timestamp
            }
            return base_response
        
        # Message 12+: SENTIMENT CHANGES TO POSITIVE!
        else:  # msg_num >= 12
            return {
                "conversation_id": conversation_id,
                "tenant_id": tenant_id,
                "sentiment": {
                    "conversation_id": conversation_id,
                    "tenant_id": tenant_id,
                    "sentiment": "positive",
                    "confidence": 0.95,
                    "emotion": "satisfied",
                    "reasoning": "The customer expresses relief and thanks, indicating satisfaction after the issue was resolved. The phrase 'That's a huge relief' clearly conveys a positive emotional state.",
                    "timestamp": timestamp
                },
                "pii": {
                    "conversation_id": conversation_id,
                    "tenant_id": tenant_id,
                    "has_pii": True,
                    "entities": [
                        {"type": "name", "value": "Sarah Lee", "start_index": 10, "end_index": 19},
                        {"type": "account_number", "value": "4421", "start_index": 35, "end_index": 39},
                        {"type": "phone", "value": "24456455", "start_index": 58, "end_index": 66}
                    ],
                    "redacted_text": message_text,
                    "timestamp": timestamp
                },
                "insights": {
                    "conversation_id": conversation_id,
                    "tenant_id": tenant_id,
                    "intent": "Account Issue",
                    "urgency": "High" if msg_num >= 14 else "Critical",
                    "categories": ["Account Access", "Technical Support"],
                    "suggested_actions": ["Apologize and acknowledge frustration", "Provide immediate resolution"],
                    "requires_escalation": False,
                    "estimated_resolution_time": "< 1 hour",
                    "key_concerns": ["Locked out of account", "Inability to pay bills on time" if msg_num >= 14 else "Inability to pay bills"],
                    "timestamp": timestamp
                },
                "summary": {
                    "conversation_id": conversation_id,
                    "tenant_id": tenant_id,
                    "tldr": "Customer account access restored; issue resolved; customer confirmed access.",
                    "customer_issue": "Customer was locked out of their bank account.",
                    "agent_response": "Account access restored.",
                    "key_points": ["Customer's account lockout resolved.", "Customer can now access their account.", "Customer confirmed account access."],
                    "next_steps": ["Monitor account activity.", "Close the support ticket."],
                    "timestamp": timestamp
                },
                "last_updated": timestamp
            }
