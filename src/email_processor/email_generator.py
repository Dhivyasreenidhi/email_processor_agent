"""
AI-powered Email Generator.

Uses Google Gemini to generate professional email drafts.
"""

import logging
from typing import Optional, List
from datetime import datetime

import google.generativeai as genai

from email_processor.config import Settings
from email_processor.models import (
    EmailDraft,
    EmailAddress,
    GenerationRequest,
    EmailPriority,
)

logger = logging.getLogger(__name__)


class EmailGenerator:
    """
    AI-powered email generator using Google Gemini.
    
    Generates professional email drafts based on purpose,
    context, and desired tone.
    """

    SYSTEM_PROMPT = """You are a professional email writing assistant. Your task is to generate 
well-structured, clear, and appropriate emails based on the user's requirements.

Follow these guidelines:
1. Write in a clear, professional tone unless otherwise specified
2. Keep emails concise but complete
3. Use proper email formatting with greeting, body, and closing
4. Adapt the tone based on the specified style (formal, casual, friendly, etc.)
5. Include all key points provided by the user
6. Use appropriate subject lines that summarize the email content

Output format:
- First line: SUBJECT: <the subject line>
- Then a blank line
- Then the email body

Do not include placeholders like [Your Name] - use the provided signature name if given,
or end with a simple closing like "Best regards" without a name if not provided.
"""

    def __init__(self, settings: Settings):
        """Initialize the email generator with settings."""
        self.settings = settings
        
        # Configure Gemini
        genai.configure(api_key=settings.google_api_key.get_secret_value())
        
        self.model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
        )
        
        logger.info("Email Generator initialized with Gemini")

    def _build_prompt(self, request: GenerationRequest) -> str:
        """Build the generation prompt from request."""
        prompt_parts = []
        
        # Include system prompt for gemini-pro compatibility
        prompt_parts.append(self.SYSTEM_PROMPT)
        prompt_parts.append("\n--- USER REQUEST ---\n")
        prompt_parts.append(f"Generate an email for the following purpose:\n{request.purpose}")
        
        if request.recipient_name:
            prompt_parts.append(f"\nRecipient name: {request.recipient_name}")
        
        prompt_parts.append(f"Recipient email: {request.recipient_email}")
        
        if request.context:
            prompt_parts.append(f"\nAdditional context: {request.context}")
        
        prompt_parts.append(f"\nDesired tone: {request.tone}")
        
        if request.key_points:
            prompt_parts.append("\nKey points to include:")
            for i, point in enumerate(request.key_points, 1):
                prompt_parts.append(f"  {i}. {point}")
        
        if request.max_length:
            prompt_parts.append(f"\nMaximum length: {request.max_length} characters")
        
        if request.include_signature and request.signature_name:
            prompt_parts.append(f"\nSign the email with: {request.signature_name}")
        elif request.include_signature:
            prompt_parts.append("\nInclude a professional closing")
        else:
            prompt_parts.append("\nDo not include a closing signature")
        
        return "\n".join(prompt_parts)

    def _parse_response(
        self,
        response_text: str,
        request: GenerationRequest
    ) -> EmailDraft:
        """Parse the AI response into an EmailDraft."""
        lines = response_text.strip().split('\n')
        
        subject = "Generated Email"
        body_start = 0
        
        # Extract subject
        for i, line in enumerate(lines):
            if line.upper().startswith("SUBJECT:"):
                subject = line[8:].strip()
                body_start = i + 1
                break
        
        # Skip blank lines after subject
        while body_start < len(lines) and not lines[body_start].strip():
            body_start += 1
        
        body = '\n'.join(lines[body_start:]).strip()
        
        return EmailDraft(
            to=[EmailAddress(
                email=request.recipient_email,
                name=request.recipient_name
            )],
            subject=subject,
            body_text=body,
            created_at=datetime.now()
        )

    def generate(self, request: GenerationRequest) -> EmailDraft:
        """
        Generate an email draft based on the request.
        
        Args:
            request: GenerationRequest with email requirements
            
        Returns:
            EmailDraft ready to be sent or edited
        """
        logger.info(f"Generating email for: {request.purpose[:50]}...")
        
        prompt = self._build_prompt(request)
        
        try:
            response = self.model.generate_content(prompt)
            
            if not response or not response.text:
                raise ValueError("Empty response from AI")
            
            draft = self._parse_response(response.text, request)
            
            logger.info(f"Generated email with subject: {draft.subject}")
            return draft
            
        except Exception as e:
            logger.error(f"Email generation failed: {e}")
            raise

    def generate_simple(
        self,
        purpose: str,
        recipient_email: str,
        recipient_name: Optional[str] = None,
        tone: str = "professional",
        signature_name: Optional[str] = None
    ) -> EmailDraft:
        """
        Generate a simple email with minimal parameters.
        
        Args:
            purpose: What the email should accomplish
            recipient_email: Recipient's email address
            recipient_name: Optional recipient name
            tone: Desired tone (professional, friendly, formal, casual)
            signature_name: Name to sign with
            
        Returns:
            EmailDraft ready to be sent or edited
        """
        request = GenerationRequest(
            purpose=purpose,
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            tone=tone,
            signature_name=signature_name,
            include_signature=True
        )
        
        return self.generate(request)

    def generate_follow_up(
        self,
        original_subject: str,
        original_context: str,
        recipient_email: str,
        recipient_name: Optional[str] = None,
        days_since: int = 7,
        signature_name: Optional[str] = None
    ) -> EmailDraft:
        """
        Generate a follow-up email.
        
        Args:
            original_subject: Subject of the original email
            original_context: Brief context of what was discussed
            recipient_email: Recipient's email
            recipient_name: Optional recipient name
            days_since: Days since original email
            signature_name: Name to sign with
            
        Returns:
            EmailDraft for the follow-up
        """
        purpose = f"""Write a polite follow-up email regarding a previous email.
        
Original email subject: {original_subject}
Original context: {original_context}
Days since the original email: {days_since}

The follow-up should:
- Reference the previous email politely
- Gently remind the recipient about the pending matter
- Offer to provide any additional information if needed
- Not sound pushy or aggressive
"""
        
        return self.generate_simple(
            purpose=purpose,
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            tone="professional and polite",
            signature_name=signature_name
        )

    def generate_introduction(
        self,
        your_name: str,
        your_role: str,
        company: str,
        purpose_of_contact: str,
        recipient_email: str,
        recipient_name: Optional[str] = None,
        recipient_company: Optional[str] = None
    ) -> EmailDraft:
        """
        Generate a professional introduction email.
        
        Args:
            your_name: Your name
            your_role: Your job title/role
            company: Your company name
            purpose_of_contact: Why you're reaching out
            recipient_email: Recipient's email
            recipient_name: Optional recipient name
            recipient_company: Optional recipient's company
            
        Returns:
            EmailDraft for the introduction
        """
        purpose = f"""Write a professional introduction email.

About me:
- Name: {your_name}
- Role: {your_role}
- Company: {company}

Purpose of reaching out: {purpose_of_contact}
"""
        
        if recipient_company:
            purpose += f"\nRecipient works at: {recipient_company}"
        
        purpose += """

The email should:
- Introduce myself briefly
- Explain why I'm reaching out
- Be engaging but not too lengthy
- Include a clear call-to-action
"""
        
        return self.generate_simple(
            purpose=purpose,
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            tone="professional and friendly",
            signature_name=your_name
        )
