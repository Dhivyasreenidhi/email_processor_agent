"""
Data models for Email Processor Agent.

Defines Pydantic models for emails, drafts, and analysis results.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr


class EmailPriority(str, Enum):
    """Email priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class EmailCategory(str, Enum):
    """Email categories for classification."""
    INQUIRY = "inquiry"
    COMPLAINT = "complaint"
    FEEDBACK = "feedback"
    SUPPORT = "support"
    SALES = "sales"
    NEWSLETTER = "newsletter"
    NOTIFICATION = "notification"
    PERSONAL = "personal"
    SPAM = "spam"
    OTHER = "other"


class SentimentType(str, Enum):
    """Sentiment analysis results."""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class EmailAttachment(BaseModel):
    """Email attachment model."""
    filename: str
    content_type: str
    size_bytes: int
    content: Optional[bytes] = Field(default=None, exclude=True)


class EmailAddress(BaseModel):
    """Email address with optional display name."""
    email: EmailStr
    name: Optional[str] = None

    def __str__(self) -> str:
        if self.name:
            return f"{self.name} <{self.email}>"
        return self.email


class EmailMessage(BaseModel):
    """Represents an email message from the inbox."""
    
    message_id: str = Field(..., description="Unique message ID")
    uid: int = Field(..., description="IMAP UID")
    subject: str = Field(default="(No Subject)")
    sender: EmailAddress = Field(..., description="From address")
    recipients: List[EmailAddress] = Field(default_factory=list, description="To addresses")
    cc: List[EmailAddress] = Field(default_factory=list, description="CC addresses")
    bcc: List[EmailAddress] = Field(default_factory=list, description="BCC addresses")
    date: datetime = Field(..., description="Email date")
    body_text: Optional[str] = Field(default=None, description="Plain text body")
    body_html: Optional[str] = Field(default=None, description="HTML body")
    attachments: List[EmailAttachment] = Field(default_factory=list)
    is_read: bool = Field(default=False)
    is_replied: bool = Field(default=False)
    labels: List[str] = Field(default_factory=list)
    
    # Threading support
    in_reply_to: Optional[str] = Field(default=None, description="In-Reply-To header")
    references: List[str] = Field(default_factory=list, description="References header")
    thread_id: Optional[str] = Field(default=None, description="Email thread ID")

    @property
    def body(self) -> str:
        """Get the best available body content."""
        return self.body_text or self.body_html or ""

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class EmailDraft(BaseModel):
    """Represents an email draft to be sent."""
    
    to: List[EmailAddress] = Field(..., description="Recipients")
    cc: List[EmailAddress] = Field(default_factory=list)
    bcc: List[EmailAddress] = Field(default_factory=list)
    subject: str = Field(..., description="Email subject")
    body_text: str = Field(..., description="Plain text body")
    body_html: Optional[str] = Field(default=None, description="HTML body")
    attachments: List[EmailAttachment] = Field(default_factory=list)
    priority: EmailPriority = Field(default=EmailPriority.NORMAL)
    
    # For replies
    in_reply_to: Optional[str] = Field(default=None)
    references: List[str] = Field(default_factory=list)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    is_reply: bool = Field(default=False)
    original_message_id: Optional[str] = Field(default=None)


class EmailAnalysis(BaseModel):
    """Analysis results for an email."""
    
    message_id: str = Field(..., description="Original message ID")
    category: EmailCategory = Field(..., description="Email category")
    priority: EmailPriority = Field(..., description="Suggested priority")
    sentiment: SentimentType = Field(..., description="Detected sentiment")
    summary: str = Field(..., description="Brief summary of the email")
    key_points: List[str] = Field(default_factory=list, description="Key points extracted")
    action_required: bool = Field(default=False, description="Whether action is needed")
    suggested_actions: List[str] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0, description="Analysis confidence")
    
    # Response generation
    suggested_response: Optional[str] = Field(default=None)
    response_tone: Optional[str] = Field(default=None)
    
    # Metadata
    analyzed_at: datetime = Field(default_factory=datetime.now)
    processing_time_ms: Optional[int] = Field(default=None)


class GenerationRequest(BaseModel):
    """Request for email generation."""
    
    purpose: str = Field(..., description="Purpose of the email")
    recipient_name: Optional[str] = Field(default=None)
    recipient_email: EmailStr = Field(..., description="Recipient email")
    context: Optional[str] = Field(default=None, description="Additional context")
    tone: str = Field(default="professional", description="Desired tone")
    key_points: List[str] = Field(default_factory=list, description="Points to include")
    max_length: Optional[int] = Field(default=None, description="Max character length")
    include_signature: bool = Field(default=True)
    signature_name: Optional[str] = Field(default=None)


class ResponseRequest(BaseModel):
    """Request for generating a response to an email."""
    
    original_email: EmailMessage = Field(..., description="Original email to respond to")
    response_intent: str = Field(..., description="Intent of the response")
    tone: str = Field(default="professional")
    include_original: bool = Field(default=True, description="Quote original email")
    additional_context: Optional[str] = Field(default=None)
