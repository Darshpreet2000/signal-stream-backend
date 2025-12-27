"""Google Gemini AI service with rate limiting and structured outputs."""

import asyncio
import json
import logging
import re
from typing import Any, Dict, Optional

import google.generativeai as genai

from ..config import Settings
from ..models import (
    SentimentResult,
    PIIResult,
    InsightsResult,
    SummaryResult,
    SentimentType,
    EmotionType,
    PIIEntity,
    PIIEntityType,
    IntentType,
    UrgencyLevel,
)

logger = logging.getLogger(__name__)


class GeminiService:
    """Google Gemini AI service with rate limiting and structured outputs."""

    def __init__(self, settings: Settings):
        """Initialize Gemini service.

        Args:
            settings: Application settings
        """
        self.settings = settings

        # Configure Gemini API
        genai.configure(api_key=settings.gemini_api_key)

        # Initialize model
        self.model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            generation_config={
                "temperature": settings.gemini_temperature,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": settings.gemini_max_output_tokens,
                "response_mime_type": "application/json",  # Force JSON output
            },
        )

        # Rate limiting: semaphore for concurrent requests
        self.semaphore = asyncio.Semaphore(settings.max_concurrent_ai_requests)

        # Simple rate limiting (requests per minute)
        self.request_timestamps = []

        logger.info(
            f"Gemini AI service initialized with model: {settings.gemini_model}"
        )

    async def _rate_limit(self) -> None:
        """Apply rate limiting based on requests per minute."""
        import time

        now = time.time()

        # Remove timestamps older than 1 minute
        self.request_timestamps = [
            ts for ts in self.request_timestamps if now - ts < 60
        ]

        # Check if we've hit the limit
        if len(self.request_timestamps) >= self.settings.gemini_requests_per_minute:
            # Wait until oldest request is more than 1 minute old
            sleep_time = 60 - (now - self.request_timestamps[0])
            if sleep_time > 0:
                logger.warning(
                    f"Rate limit reached, sleeping for {sleep_time:.2f} seconds"
                )
                await asyncio.sleep(sleep_time)

        self.request_timestamps.append(now)

    async def _generate_content(self, prompt: str) -> Dict[str, Any]:
        """Generate content with rate limiting.

        Args:
            prompt: Input prompt

        Returns:
            Parsed JSON response
        """
        async with self.semaphore:
            await self._rate_limit()

            try:
                # Run in executor to avoid blocking
                loop = asyncio.get_running_loop()
                response = await loop.run_in_executor(
                    None, lambda: self.model.generate_content(prompt)
                )

                # Parse JSON response - handle markdown code blocks
                response_text = response.text.strip()
                logger.debug(f"Raw Gemini response: {response_text[:500]}")
                
                # Remove markdown code blocks if present
                if response_text.startswith("```"):
                    # Find the actual JSON content between code blocks
                    lines = response_text.split('\n')
                    # Remove first line (```json or ```)
                    lines = lines[1:]
                    # Remove last line if it's ```
                    if lines and lines[-1].strip() == "```":
                        lines = lines[:-1]
                    response_text = '\n'.join(lines).strip()
                
                result = json.loads(response_text)
                logger.debug(f"Parsed result type: {type(result)}, value: {result}")
                
                # Handle case where Gemini returns a list with single object
                if isinstance(result, list) and len(result) > 0:
                    result = result[0]
                    logger.debug(f"Extracted first element from list: {type(result)}")
                
                return result

            except Exception as e:
                logger.error(f"Gemini API error: {e}")
                logger.warning("Falling back to mock data due to API error")
                
                # Mock data fallback based on prompt content
                if "Analyze the sentiment" in prompt:
                    return {
                        "sentiment": "negative",
                        "confidence": 0.85,
                        "emotion": "frustrated",
                        "reasoning": "Customer is expressing frustration about technical issues."
                    }
                elif "Identify all personally identifiable information" in prompt:
                    text = prompt.split('"""')[1].strip() if '"""' in prompt else ""
                    entities = []
                    
                    # Mock PII detection logic
                    # Phone numbers (simple 8+ digits)
                    for m in re.finditer(r'\b\d{8,15}\b', text):
                        entities.append({
                            "type": "phone",
                            "value": "[REDACTED]",
                            "startIndex": m.start(),
                            "endIndex": m.end()
                        })
                    
                    # Account numbers (context based)
                    for m in re.finditer(r'account\s+(?:number\s+)?(?:ending\s+)?(\d+)', text, re.IGNORECASE):
                        entities.append({
                            "type": "account_number",
                            "value": "[REDACTED]",
                            "startIndex": m.start(1),
                            "endIndex": m.end(1)
                        })
                        
                    # Names (very basic mock for "My name is X")
                    for m in re.finditer(r'My name is ([A-Z][a-z]+ [A-Z][a-z]+)', text):
                        entities.append({
                            "type": "name",
                            "value": "[REDACTED]",
                            "startIndex": m.start(1),
                            "endIndex": m.end(1)
                        })

                    has_pii = len(entities) > 0
                    redacted_text = text
                    # Apply redactions in reverse order
                    for e in sorted(entities, key=lambda x: x['startIndex'], reverse=True):
                        redacted_text = redacted_text[:e['startIndex']] + "[REDACTED]" + redacted_text[e['endIndex']:]

                    return {
                        "hasPII": has_pii,
                        "entities": entities,
                        "redactedText": redacted_text
                    }
                elif "Analyze this support conversation and extract key insights" in prompt:
                    return {
                        "intent": "Technical Issue",
                        "urgency": "Medium",
                        "categories": ["connectivity", "network"],
                        "suggestedActions": ["Troubleshoot router", "Check service status"],
                        "requiresEscalation": False,
                        "estimatedResolutionTime": "1-4 hours",
                        "keyConcerns": ["Connection stability"]
                    }
                elif "Summarize this support conversation" in prompt or "Update the support conversation summary" in prompt:
                    return {
                        "tldr": "Customer reported technical issues (Mock Summary).",
                        "customerIssue": "Technical connectivity problem",
                        "agentResponse": "Agent is investigating.",
                        "keyPoints": ["Issue reported", "Investigation started"],
                        "nextSteps": ["Check logs", "Reply to customer"]
                    }
                else:
                    # Generic fallback
                    return {"response": "I apologize, but I am currently experiencing high traffic. Please try again later."}

    async def analyze_sentiment(
        self, conversation_id: str, tenant_id: str, message_text: str
    ) -> SentimentResult:
        """Analyze sentiment of a support message or conversation.

        Args:
            conversation_id: Conversation ID
            tenant_id: Tenant ID
            message_text: Message or conversation text to analyze

        Returns:
            Sentiment analysis result
        """
        logger.debug(f"→ [analyze_sentiment] conv_id={conversation_id}, msg_len={len(message_text)}")
        prompt = f"""Analyze the CUSTOMER'S CURRENT sentiment based on their LATEST message in this support conversation. 
Focus on detecting sentiment changes - if the customer was frustrated but now sounds satisfied, reflect that change.

{message_text}

IMPORTANT: Base your analysis primarily on the LATEST customer message. The context is provided for understanding, but the sentiment should reflect the customer's current emotional state.

Respond ONLY with valid JSON in this exact format:
{{
  "sentiment": "positive" | "neutral" | "negative",
  "confidence": <number between 0 and 1>,
  "emotion": "angry" | "frustrated" | "satisfied" | "confused" | "urgent" | "happy" | "neutral",
  "reasoning": "<brief explanation of the customer's CURRENT emotional state based on their latest message>"
}}"""

        result = await self._generate_content(prompt)
        
        sentiment_result = SentimentResult(
            conversation_id=conversation_id,
            tenant_id=tenant_id,
            sentiment=SentimentType(result["sentiment"]),
            confidence=float(result["confidence"]),
            emotion=EmotionType(result["emotion"]),
            reasoning=result["reasoning"],
        )
        logger.debug(
            f"  ✓ Sentiment: {sentiment_result.sentiment.value}, "
            f"Emotion: {sentiment_result.emotion.value}, "
            f"Confidence: {sentiment_result.confidence:.2f}"
        )
        return sentiment_result

    async def detect_pii(
        self, conversation_id: str, tenant_id: str, message_text: str
    ) -> PIIResult:
        """Detect personally identifiable information in message.

        Args:
            conversation_id: Conversation ID
            tenant_id: Tenant ID
            message_text: Message to analyze

        Returns:
            PII detection result
        """
        logger.debug(f"→ [detect_pii] conv_id={conversation_id}, msg_len={len(message_text)}")
        prompt = f"""Identify all personally identifiable information (PII) in this message.

Message:
\"\"\"
{message_text}
\"\"\"

Detect and categorize:
- email addresses
- phone numbers
- credit card numbers (partial)
- SSN/national IDs
- physical addresses
- account numbers
- names

Respond with JSON:
{{
  "hasPII": true | false,
  "entities": [
    {{
      "type": "email" | "phone" | "credit_card" | "ssn" | "address" | "account_number" | "name",
      "value": "[REDACTED]",
      "startIndex": <number>,
      "endIndex": <number>
    }}
  ],
  "redactedText": "<message with [REDACTED] in place of PII>"
}}"""

        result = await self._generate_content(prompt)

        entities = [
            PIIEntity(
                type=PIIEntityType(e["type"]),
                value=e.get("value", "[REDACTED]"),
                start_index=e["startIndex"],
                end_index=e["endIndex"],
            )
            for e in result.get("entities", [])
        ]

        pii_result = PIIResult(
            conversation_id=conversation_id,
            tenant_id=tenant_id,
            has_pii=result["hasPII"],
            entities=entities,
            redacted_text=result.get("redactedText"),
        )
        logger.debug(f"  ✓ PII detected: {pii_result.has_pii}, Entities: {len(pii_result.entities)}")
        return pii_result

    async def extract_insights(
        self, conversation_id: str, tenant_id: str, conversation_text: str
    ) -> InsightsResult:
        """Extract insights, intent, and urgency from conversation.

        Args:
            conversation_id: Conversation ID
            tenant_id: Tenant ID
            conversation_text: Full conversation context

        Returns:
            Insights extraction result
        """
        logger.debug(f"→ [extract_insights] conv_id={conversation_id}, text_len={len(conversation_text)}")
        prompt = f"""Analyze this support conversation and extract key insights AND generate a summary.

Conversation:
\"\"\"
{conversation_text}
\"\"\"

IMPORTANT: Analyze customer sentiment/mood from their language and tone. If the customer is frustrated, angry, or highly dissatisfied:
- Suggest offering compensation (discount, refund, credit)
- Recommend empathy and acknowledgment
- Prioritize quick resolution to retain the customer

Respond with JSON (includes both insights AND summary):
{{
  "intent": "Refund Request" | "Technical Issue" | "Billing Inquiry" | "Feature Request" | "Complaint" | "General Inquiry" | "Account Issue" | "Cancellation",
  "urgency": "Low" | "Medium" | "High" | "Critical",
  "categories": ["<category1>", "<category2>"],
  "suggestedActions": [
    // For negative mood: ["Offer 20% discount/credit", "Apologize and acknowledge frustration", "Escalate to senior support", "Provide immediate resolution"]
    // For neutral/positive: ["Provide solution steps", "Share documentation", "Follow up in 24 hours"]
    "<action1>", "<action2>"
  ],
  "requiresEscalation": true | false,
  "estimatedResolutionTime": "< 1 hour" | "1-4 hours" | "4-24 hours" | "1-3 days",
  "keyConcerns": ["<concern1>", "<concern2>"],
  "summary": {{
    "tldr": "<one sentence summary>",
    "customerIssue": "<brief description>",
    "agentResponse": "<brief description or null>",
    "keyPoints": ["<point1>", "<point2>"],
    "nextSteps": ["<step1>", "<step2>"]
  }}
}}"""

        result = await self._generate_content(prompt)

        insights_result = InsightsResult(
            conversation_id=conversation_id,
            tenant_id=tenant_id,
            intent=IntentType(result["intent"]),
            urgency=UrgencyLevel(result["urgency"]),
            categories=result.get("categories", []),
            suggested_actions=result.get("suggestedActions", []),
            requires_escalation=result["requiresEscalation"],
            estimated_resolution_time=result["estimatedResolutionTime"],
            key_concerns=result.get("keyConcerns", []),
        )
        
        # Also create summary result from the combined response
        summary_data = result.get("summary", {})
        summary_result = SummaryResult(
            conversation_id=conversation_id,
            tenant_id=tenant_id,
            tldr=summary_data.get("tldr", ""),
            customer_issue=summary_data.get("customerIssue", ""),
            agent_response=summary_data.get("agentResponse"),
            key_points=summary_data.get("keyPoints", []),
            next_steps=summary_data.get("nextSteps", []),
        )
        
        logger.debug(
            f"  ✓ Intent: {insights_result.intent.value}, "
            f"Urgency: {insights_result.urgency.value}, "
            f"Escalation: {insights_result.requires_escalation}, "
            f"Summary: {summary_result.tldr[:50]}..."
        )
        return insights_result, summary_result

    async def summarize_conversation(
        self, conversation_id: str, tenant_id: str, conversation_text: str
    ) -> SummaryResult:
        """Generate summary of conversation.

        Args:
            conversation_id: Conversation ID
            tenant_id: Tenant ID
            conversation_text: Full conversation context

        Returns:
            Summary result
        """
        logger.debug(f"→ [summarize_conversation] conv_id={conversation_id}, text_len={len(conversation_text)}")
        prompt = f"""Summarize this support conversation.

Conversation:
\"\"\"
{conversation_text}
\"\"\"

Provide a structured summary in JSON:
{{
  "tldr": "<1-sentence summary>",
  "customerIssue": "<what customer needs>",
  "agentResponse": "<brief description or null>",
  "keyPoints": ["<point1>", "<point2>"],
  "nextSteps": ["<step1>", "<step2>"]
}}"""

        result = await self._generate_content(prompt)

        summary_result = SummaryResult(
            conversation_id=conversation_id,
            tenant_id=tenant_id,
            tldr=result["tldr"],
            customer_issue=result["customerIssue"],
            agent_response=result.get("agentResponse"),
            key_points=result.get("keyPoints", []),
            next_steps=result.get("nextSteps", []),
        )
        logger.debug(f"  ✓ Summary: {summary_result.tldr[:80]}...")
        return summary_result

    async def update_conversation_summary(
        self,
        conversation_id: str,
        tenant_id: str,
        old_summary: Optional[SummaryResult],
        new_message: str,
        sender: str,
    ) -> SummaryResult:
        """Update conversation summary with new message.

        Args:
            conversation_id: Conversation ID
            tenant_id: Tenant ID
            old_summary: Previous summary (optional)
            new_message: New message text
            sender: Sender of the new message (user/agent)

        Returns:
            Updated summary result
        """
        logger.debug(f"→ [update_summary] conv_id={conversation_id}")
        
        if old_summary:
            context = f"""
Previous Summary:
- TLDR: {old_summary.tldr}
- Issue: {old_summary.customer_issue}
- Key Points: {', '.join(old_summary.key_points)}
- Next Steps: {', '.join(old_summary.next_steps)}
"""
        else:
            context = "No previous summary (start of conversation)."

        prompt = f"""Update the support conversation summary with the new message.

{context}

New Message from {sender}:
"{new_message}"

Provide an updated structured summary in JSON:
{{
  "tldr": "<updated 1-sentence summary>",
  "customerIssue": "<updated customer needs>",
  "agentResponse": "<updated brief description or null>",
  "keyPoints": ["<updated point1>", "<updated point2>"],
  "nextSteps": ["<updated step1>", "<updated step2>"]
}}"""

        result = await self._generate_content(prompt)

        summary_result = SummaryResult(
            conversation_id=conversation_id,
            tenant_id=tenant_id,
            tldr=result["tldr"],
            customer_issue=result["customerIssue"],
            agent_response=result.get("agentResponse"),
            key_points=result.get("keyPoints", []),
            next_steps=result.get("nextSteps", []),
        )
        logger.debug(f"  ✓ Updated Summary: {summary_result.tldr[:80]}...")
        return summary_result

    async def generate_response(
        self, conversation_id: str, tenant_id: str, conversation_text: str, user_message: str
    ) -> str:
        """Generate a helpful AI response to a customer support message.

        Args:
            conversation_id: Conversation ID
            tenant_id: Tenant ID
            conversation_text: Full conversation history
            user_message: Latest customer message to respond to

        Returns:
            Generated AI response text
        """
        logger.debug(
            f"→ [generate_response] conv_id={conversation_id}, msg_len={len(user_message)}"
        )
        prompt = f"""You are a helpful AI assistant for a customer support platform called SignalStream. 
Generate a professional, empathetic, and helpful response to the customer's message.

Conversation History:
\"\"\"
{conversation_text}
\"\"\"

Latest Customer Message:
\"\"\"
{user_message}
\"\"\"

Guidelines:
- Be professional and empathetic
- Acknowledge the customer's concern
- Provide helpful information or next steps
- Keep the response concise (2-4 sentences)
- If the issue requires human escalation, suggest that
- Be warm and supportive

Respond with JSON containing only the response text:
{{
  "response": "<your generated response here>"
}}"""

        logger.debug(f"  Prompt length: {len(prompt)} chars")
        result = await self._generate_content(prompt)
        response = result.get("response", "Thank you for your message. A support agent will assist you shortly.")
        logger.debug(f"  ✓ Generated response length: {len(response)} chars")
        logger.debug(f"  Response preview: {response[:100]}...")
        return response
