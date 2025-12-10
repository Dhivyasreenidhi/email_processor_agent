"""
Gmail SMTP Client for sending emails.

Provides a robust SMTP client for sending emails through Gmail.
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formataddr, formatdate, make_msgid
from typing import Optional
from contextlib import contextmanager

from email_processor.config import Settings
from email_processor.models import EmailDraft, EmailPriority

logger = logging.getLogger(__name__)


class SMTPError(Exception):
    """Custom exception for SMTP operations."""
    pass


class GmailSMTPClient:
    """
    Gmail SMTP client for sending emails.
    
    Supports:
    - Plain text and HTML emails
    - Attachments
    - Reply threading
    - Priority settings
    """

    def __init__(self, settings: Settings):
        """Initialize the SMTP client with settings."""
        self.settings = settings
        self._connection: Optional[smtplib.SMTP] = None

    @contextmanager
    def connect(self):
        """Context manager for SMTP connection."""
        try:
            logger.info(f"Connecting to {self.settings.smtp_server}:{self.settings.smtp_port}")
            
            self._connection = smtplib.SMTP(
                self.settings.smtp_server,
                self.settings.smtp_port
            )
            
            # Start TLS if configured
            if self.settings.smtp_use_tls:
                self._connection.starttls()
            
            # Authenticate
            self._connection.login(
                self.settings.gmail_email,
                self.settings.gmail_app_password.get_secret_value()
            )
            logger.info("Successfully authenticated with Gmail SMTP")
            
            yield self
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {e}")
            raise SMTPError(f"Authentication failed: {e}")
        except Exception as e:
            logger.error(f"SMTP connection error: {e}")
            raise SMTPError(f"Connection failed: {e}")
        finally:
            if self._connection:
                try:
                    self._connection.quit()
                    logger.info("Disconnected from SMTP server")
                except:
                    pass
                self._connection = None

    def _create_message(self, draft: EmailDraft) -> MIMEMultipart:
        """Create MIME message from draft."""
        # Create message container
        if draft.body_html:
            msg = MIMEMultipart("alternative")
        else:
            msg = MIMEMultipart()

        # Set headers
        msg["From"] = self.settings.gmail_email
        msg["To"] = ", ".join(str(addr) for addr in draft.to)
        
        if draft.cc:
            msg["Cc"] = ", ".join(str(addr) for addr in draft.cc)
        
        msg["Subject"] = draft.subject
        msg["Date"] = formatdate(localtime=True)
        msg["Message-ID"] = make_msgid()

        # Set priority
        if draft.priority == EmailPriority.HIGH:
            msg["X-Priority"] = "1"
            msg["Importance"] = "high"
        elif draft.priority == EmailPriority.URGENT:
            msg["X-Priority"] = "1"
            msg["Importance"] = "high"
            msg["X-MSMail-Priority"] = "High"
        elif draft.priority == EmailPriority.LOW:
            msg["X-Priority"] = "5"
            msg["Importance"] = "low"

        # Threading headers for replies
        if draft.in_reply_to:
            msg["In-Reply-To"] = draft.in_reply_to
        
        if draft.references:
            msg["References"] = " ".join(draft.references)

        # Add text body
        text_part = MIMEText(draft.body_text, "plain", "utf-8")
        msg.attach(text_part)

        # Add HTML body if present
        if draft.body_html:
            html_part = MIMEText(draft.body_html, "html", "utf-8")
            msg.attach(html_part)

        # Add attachments
        for attachment in draft.attachments:
            if attachment.content:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.content)
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={attachment.filename}"
                )
                msg.attach(part)

        return msg

    def send(self, draft: EmailDraft) -> str:
        """
        Send an email from draft.
        
        Returns the message ID of the sent email.
        """
        if not self._connection:
            raise SMTPError("Not connected")

        msg = self._create_message(draft)
        
        # Collect all recipients
        recipients = [str(addr.email) for addr in draft.to]
        recipients.extend(str(addr.email) for addr in draft.cc)
        recipients.extend(str(addr.email) for addr in draft.bcc)

        try:
            self._connection.sendmail(
                self.settings.gmail_email,
                recipients,
                msg.as_string()
            )
            
            message_id = msg["Message-ID"]
            logger.info(f"Email sent successfully: {message_id}")
            logger.info(f"  To: {', '.join(str(addr) for addr in draft.to)}")
            logger.info(f"  Subject: {draft.subject}")
            
            return message_id
            
        except smtplib.SMTPException as e:
            logger.error(f"Failed to send email: {e}")
            raise SMTPError(f"Send failed: {e}")

    def send_simple(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> str:
        """Send a simple email without creating a draft object."""
        from email_processor.models import EmailAddress
        
        draft = EmailDraft(
            to=[EmailAddress(email=to)],
            subject=subject,
            body_text=body,
            body_html=html_body
        )
        
        return self.send(draft)
