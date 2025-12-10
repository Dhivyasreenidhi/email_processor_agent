"""
AI-powered Email Analyser.

Uses Google Gemini to analyze incoming emails and generate intelligent responses.
"""

import json
import logging
import time
from typing import Optional, List
from datetime import datetime

import google.generativeai as genai

from email_processor.config import Settings
from email_processor.models import (
    EmailMessage,
    EmailDraft,
    EmailAddress,
    EmailAnalysis,
    EmailCategory,
    EmailPriority,
    SentimentType,
    ResponseRequest,
)

logger = logging.getLogger(__name__)


class EmailAnalyser:
    """
    AI-powered email analyser using Google Gemini.
    
    Analyzes incoming emails to:
    - Categorize emails
    - Detect sentiment
    - Extract key points
    - Suggest actions
    - Generate intelligent responses
    """

    ANALYSIS_SYSTEM_PROMPT = """You are an intelligent email analysis assistant. Your task is to 
analyze emails and provide structured insights.

For each email, you will analyze:
1. Category: Classify the email into one of these categories:
   - inquiry: Questions or requests for information
   - complaint: Customer complaints or issues
   - feedback: Feedback or reviews
   - support: Technical support requests
   - sales: Sales or business inquiries
   - newsletter: Newsletters or promotional content
   - notification: Automated notifications
   - personal: Personal emails
   - spam: Spam or unwanted emails
   - other: Emails that don't fit other categories

2. Priority: Assess urgency level:
   - urgent: Requires immediate attention
   - high: Important, should be addressed soon
   - normal: Regular priority
   - low: Can be addressed later

3. Sentiment: Determine emotional tone:
   - positive: Happy, satisfied, grateful
   - neutral: Factual, informational
   - negative: Upset, frustrated, disappointed

4. Summary: Brief 1-2 sentence summary
5. Key Points: Main points from the email (max 5)
6. Action Required: Whether the email needs a response or action
7. Suggested Actions: What actions should be taken (max 3)

You MUST respond with valid JSON in this exact format:
{
    "category": "inquiry|complaint|feedback|support|sales|newsletter|notification|personal|spam|other",
    "priority": "urgent|high|normal|low",
    "sentiment": "positive|neutral|negative",
    "summary": "Brief summary of the email",
    "key_points": ["point 1", "point 2"],
    "action_required": true|false,
    "suggested_actions": ["action 1", "action 2"]
}
"""

    RESPONSE_SYSTEM_PROMPT = """You are a professional email response assistant. Your task is to 
generate appropriate responses to emails based on the provided context and intent.

Guidelines:
1. Match the appropriate tone (professional, friendly, formal, etc.)
2. Address all points raised in the original email
3. Be helpful and solution-oriented
4. Keep responses concise but complete
5. Use proper email formatting with greeting and closing

Output format:
- First line: SUBJECT: <the subject line - usually "Re: " + original subject>
- Then a blank line
- Then the response body

If the original email is included for reference, quote relevant parts when needed.
Do not include placeholders - write a complete, ready-to-send response.
"""

    def __init__(self, settings: Settings):
        """Initialize the email analyser with settings."""
        self.settings = settings
        
        # Configure Gemini
        genai.configure(api_key=settings.google_api_key.get_secret_value())
        
        self.analysis_model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
        )
        
        self.response_model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
        )
        
        logger.info("Email Analyser initialized with Gemini")

    def _build_analysis_prompt(self, email: EmailMessage) -> str:
        """Build the analysis prompt from email."""
        prompt = f"""{self.ANALYSIS_SYSTEM_PROMPT}

--- EMAIL TO ANALYZE ---

From: {email.sender}
Subject: {email.subject}
Date: {email.date.isoformat()}

Email Body:
---
{email.body[:5000]}
---

Provide your analysis as JSON.
"""
        return prompt

    def _parse_analysis_response(
        self,
        response_text: str,
        email: EmailMessage,
        processing_time_ms: int
    ) -> EmailAnalysis:
        """Parse the AI analysis response."""
        try:
            # Try to extract JSON from response
            text = response_text.strip()
            
            # Handle code blocks
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            
            data = json.loads(text)
            
            return EmailAnalysis(
                message_id=email.message_id,
                category=EmailCategory(data.get("category", "other")),
                priority=EmailPriority(data.get("priority", "normal")),
                sentiment=SentimentType(data.get("sentiment", "neutral")),
                summary=data.get("summary", "No summary available"),
                key_points=data.get("key_points", [])[:5],
                action_required=data.get("action_required", False),
                suggested_actions=data.get("suggested_actions", [])[:3],
                confidence_score=0.85,  # Default confidence
                analyzed_at=datetime.now(),
                processing_time_ms=processing_time_ms
            )
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse AI response as JSON: {e}")
            # Return basic analysis on parse failure
            return EmailAnalysis(
                message_id=email.message_id,
                category=EmailCategory.OTHER,
                priority=EmailPriority.NORMAL,
                sentiment=SentimentType.NEUTRAL,
                summary="Analysis failed - unable to parse response",
                key_points=[],
                action_required=False,
                suggested_actions=[],
                confidence_score=0.0,
                analyzed_at=datetime.now(),
                processing_time_ms=processing_time_ms
            )

    def analyze(self, email: EmailMessage) -> EmailAnalysis:
        """
        Analyze an email and return structured insights.
        
        Args:
            email: EmailMessage to analyze
            
        Returns:
            EmailAnalysis with category, sentiment, and suggestions
        """
        logger.info(f"Analyzing email: {email.subject[:50]}...")
        
        start_time = time.time()
        prompt = self._build_analysis_prompt(email)
        
        try:
            response = self.analysis_model.generate_content(prompt)
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            if not response or not response.text:
                raise ValueError("Empty response from AI")
            
            analysis = self._parse_analysis_response(
                response.text,
                email,
                processing_time_ms
            )
            
            logger.info(f"Analysis complete: {analysis.category.value} | {analysis.sentiment.value}")
            return analysis
            
        except Exception as e:
            logger.error(f"Email analysis failed: {e}")
            raise

    def analyze_batch(self, emails: List[EmailMessage]) -> List[EmailAnalysis]:
        """
        Analyze multiple emails.
        
        Args:
            emails: List of EmailMessage objects
            
        Returns:
            List of EmailAnalysis objects
        """
        results = []
        for email in emails:
            try:
                analysis = self.analyze(email)
                results.append(analysis)
            except Exception as e:
                logger.error(f"Failed to analyze email {email.message_id}: {e}")
        
        return results

    def _build_response_prompt(self, request: ResponseRequest) -> str:
        """Build the response generation prompt."""
        email = request.original_email
        
        prompt = f"""{self.RESPONSE_SYSTEM_PROMPT}

--- EMAIL TO RESPOND TO ---

From: {email.sender}
Subject: {email.subject}
Date: {email.date.isoformat()}

Original Email:
---
{email.body[:5000]}
---

Response Requirements:
- Intent: {request.response_intent}
- Tone: {request.tone}
"""
        
        if request.additional_context:
            prompt += f"\nAdditional Context: {request.additional_context}"
        
        if request.include_original:
            prompt += "\n\nInclude a quote of the relevant part of the original email in the response."
        
        return prompt

    def _parse_response_draft(
        self,
        response_text: str,
        original_email: EmailMessage
    ) -> EmailDraft:
        """Parse the AI response into an EmailDraft."""
        lines = response_text.strip().split('\n')
        
        # Default subject is Re: original subject
        subject = f"Re: {original_email.subject}"
        body_start = 0
        
        # Extract subject if provided
        for i, line in enumerate(lines):
            if line.upper().startswith("SUBJECT:"):
                subject = line[8:].strip()
                body_start = i + 1
                break
        
        # Skip blank lines after subject
        while body_start < len(lines) and not lines[body_start].strip():
            body_start += 1
        
        body = '\n'.join(lines[body_start:]).strip()
        
        # Build references chain for threading
        references = list(original_email.references)
        if original_email.message_id not in references:
            references.append(original_email.message_id)
        
        return EmailDraft(
            to=[original_email.sender],
            subject=subject,
            body_text=body,
            in_reply_to=original_email.message_id,
            references=references,
            is_reply=True,
            original_message_id=original_email.message_id,
            created_at=datetime.now()
        )

    def generate_response(self, request: ResponseRequest) -> EmailDraft:
        """
        Generate a response to an email.
        
        Args:
            request: ResponseRequest with original email and intent
            
        Returns:
            EmailDraft with the generated response
        """
        logger.info(f"Generating response to: {request.original_email.subject[:50]}...")
        
        prompt = self._build_response_prompt(request)
        
        try:
            response = self.response_model.generate_content(prompt)
            
            if not response or not response.text:
                raise ValueError("Empty response from AI")
            
            draft = self._parse_response_draft(response.text, request.original_email)
            
            logger.info(f"Generated response with subject: {draft.subject}")
            return draft
            
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            raise

    def generate_response_simple(
        self,
        email: EmailMessage,
        intent: str,
        tone: str = "professional"
    ) -> EmailDraft:
        """
        Generate a simple response to an email.
        
        Args:
            email: Original email to respond to
            intent: What the response should accomplish
            tone: Desired tone of the response
            
        Returns:
            EmailDraft with the response
        """
        request = ResponseRequest(
            original_email=email,
            response_intent=intent,
            tone=tone,
            include_original=True
        )
        
        return self.generate_response(request)

    def suggest_response(
        self,
        email: EmailMessage,
        analysis: Optional[EmailAnalysis] = None
    ) -> EmailDraft:
        """
        Automatically suggest an appropriate response based on email analysis.
        
        Args:
            email: Email to respond to
            analysis: Optional pre-computed analysis
            
        Returns:
            EmailDraft with suggested response
        """
        # Analyze email if not provided
        if not analysis:
            analysis = self.analyze(email)
        
        # Determine response intent based on category and sentiment
        intent_map = {
            EmailCategory.INQUIRY: "Answer the questions and provide helpful information",
            EmailCategory.COMPLAINT: "Acknowledge the issue, apologize, and offer a solution",
            EmailCategory.FEEDBACK: "Thank them for the feedback and acknowledge their points",
            EmailCategory.SUPPORT: "Provide helpful guidance or troubleshooting steps",
            EmailCategory.SALES: "Respond professionally and address their business interest",
            EmailCategory.PERSONAL: "Respond in a friendly, personal manner",
        }
        
        intent = intent_map.get(
            analysis.category,
            "Provide a helpful and appropriate response"
        )
        
        # Adjust tone based on sentiment
        if analysis.sentiment == SentimentType.NEGATIVE:
            tone = "empathetic and solution-oriented"
        elif analysis.sentiment == SentimentType.POSITIVE:
            tone = "warm and appreciative"
        else:
            tone = "professional and helpful"
        
        # Add analysis context
        additional_context = f"""
Analysis Summary: {analysis.summary}
Key Points: {', '.join(analysis.key_points)}
Suggested Actions: {', '.join(analysis.suggested_actions)}
"""
        
        request = ResponseRequest(
            original_email=email,
            response_intent=intent,
            tone=tone,
            include_original=True,
            additional_context=additional_context
        )
        
        draft = self.generate_response(request)
        
        # Store analysis context in draft
        analysis.suggested_response = draft.body_text
        analysis.response_tone = tone
        
        return draft
