"""
Gmail IMAP Client for reading emails.

Provides a robust IMAP client for connecting to Gmail and fetching emails.
"""

import email
import imaplib
import logging
from datetime import datetime
from email.header import decode_header
from email.utils import parseaddr, parsedate_to_datetime
from typing import List, Optional, Tuple, Generator
from contextlib import contextmanager

from bs4 import BeautifulSoup
import html2text

from email_processor.config import Settings
from email_processor.models import (
    EmailMessage,
    EmailAddress,
    EmailAttachment,
)

logger = logging.getLogger(__name__)


class IMAPError(Exception):
    """Custom exception for IMAP operations."""
    pass


class GmailIMAPClient:
    """
    Gmail IMAP client for reading and managing emails.
    
    Supports:
    - Fetching emails from inbox
    - Filtering by read/unread status
    - Searching emails
    - Marking emails as read/unread
    - Moving emails to folders
    """

    def __init__(self, settings: Settings):
        """Initialize the IMAP client with settings."""
        self.settings = settings
        self._connection: Optional[imaplib.IMAP4_SSL] = None
        self._h2t = html2text.HTML2Text()
        self._h2t.ignore_links = False
        self._h2t.ignore_images = True

    @contextmanager
    def connect(self):
        """Context manager for IMAP connection."""
        try:
            logger.info(f"Connecting to {self.settings.imap_server}:{self.settings.imap_port}")
            
            if self.settings.imap_use_ssl:
                self._connection = imaplib.IMAP4_SSL(
                    self.settings.imap_server,
                    self.settings.imap_port
                )
            else:
                self._connection = imaplib.IMAP4(
                    self.settings.imap_server,
                    self.settings.imap_port
                )

            # Login
            self._connection.login(
                self.settings.gmail_email,
                self.settings.gmail_app_password.get_secret_value()
            )
            logger.info("Successfully authenticated with Gmail")
            
            yield self
            
        except imaplib.IMAP4.error as e:
            logger.error(f"IMAP authentication failed: {e}")
            raise IMAPError(f"Authentication failed: {e}")
        except Exception as e:
            logger.error(f"IMAP connection error: {e}")
            raise IMAPError(f"Connection failed: {e}")
        finally:
            if self._connection:
                try:
                    self._connection.logout()
                    logger.info("Disconnected from IMAP server")
                except:
                    pass
                self._connection = None

    def _decode_header_value(self, value: str) -> str:
        """Decode email header value."""
        if not value:
            return ""
        
        decoded_parts = []
        for part, encoding in decode_header(value):
            if isinstance(part, bytes):
                try:
                    decoded_parts.append(part.decode(encoding or 'utf-8', errors='replace'))
                except:
                    decoded_parts.append(part.decode('utf-8', errors='replace'))
            else:
                decoded_parts.append(str(part))
        
        return ''.join(decoded_parts)

    def _parse_email_address(self, addr_string: str) -> EmailAddress:
        """Parse email address string into EmailAddress object."""
        name, email = parseaddr(addr_string)
        name = self._decode_header_value(name) if name else None
        return EmailAddress(email=email or addr_string, name=name)

    def _parse_email_addresses(self, header_value: Optional[str]) -> List[EmailAddress]:
        """Parse multiple email addresses from header."""
        if not header_value:
            return []
        
        addresses = []
        for addr in header_value.split(','):
            addr = addr.strip()
            if addr:
                try:
                    addresses.append(self._parse_email_address(addr))
                except:
                    pass
        return addresses

    def _extract_body(self, msg: email.message.Message) -> Tuple[Optional[str], Optional[str]]:
        """Extract text and HTML body from email message."""
        text_body = None
        html_body = None

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))

                # Skip attachments
                if "attachment" in content_disposition:
                    continue

                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or 'utf-8'
                        decoded = payload.decode(charset, errors='replace')
                        
                        if content_type == "text/plain" and not text_body:
                            text_body = decoded
                        elif content_type == "text/html" and not html_body:
                            html_body = decoded
                except Exception as e:
                    logger.warning(f"Failed to decode email part: {e}")
        else:
            content_type = msg.get_content_type()
            try:
                payload = msg.get_payload(decode=True)
                if payload:
                    charset = msg.get_content_charset() or 'utf-8'
                    decoded = payload.decode(charset, errors='replace')
                    
                    if content_type == "text/plain":
                        text_body = decoded
                    elif content_type == "text/html":
                        html_body = decoded
            except Exception as e:
                logger.warning(f"Failed to decode email body: {e}")

        # Convert HTML to text if no text body
        if html_body and not text_body:
            try:
                text_body = self._h2t.handle(html_body)
            except:
                soup = BeautifulSoup(html_body, 'html.parser')
                text_body = soup.get_text(separator='\n', strip=True)

        return text_body, html_body

    def _extract_attachments(self, msg: email.message.Message) -> List[EmailAttachment]:
        """Extract attachments from email message."""
        attachments = []

        if not msg.is_multipart():
            return attachments

        for part in msg.walk():
            content_disposition = str(part.get("Content-Disposition", ""))
            
            if "attachment" in content_disposition or part.get_filename():
                filename = part.get_filename()
                if filename:
                    filename = self._decode_header_value(filename)
                    content_type = part.get_content_type()
                    payload = part.get_payload(decode=True)
                    
                    if payload:
                        attachments.append(EmailAttachment(
                            filename=filename,
                            content_type=content_type,
                            size_bytes=len(payload),
                            content=payload
                        ))

        return attachments

    def _parse_email(self, uid: int, raw_email: bytes) -> Optional[EmailMessage]:
        """Parse raw email bytes into EmailMessage object."""
        try:
            msg = email.message_from_bytes(raw_email)
            
            # Extract headers
            message_id = msg.get("Message-ID", f"<{uid}@local>")
            subject = self._decode_header_value(msg.get("Subject", "(No Subject)"))
            
            # Parse date
            date_str = msg.get("Date")
            try:
                date = parsedate_to_datetime(date_str) if date_str else datetime.now()
            except:
                date = datetime.now()

            # Parse addresses
            sender = self._parse_email_address(msg.get("From", ""))
            recipients = self._parse_email_addresses(msg.get("To"))
            cc = self._parse_email_addresses(msg.get("Cc"))
            bcc = self._parse_email_addresses(msg.get("Bcc"))

            # Extract body
            text_body, html_body = self._extract_body(msg)

            # Extract attachments
            attachments = self._extract_attachments(msg)

            # Threading headers
            in_reply_to = msg.get("In-Reply-To")
            references_header = msg.get("References", "")
            references = [ref.strip() for ref in references_header.split() if ref.strip()]

            return EmailMessage(
                message_id=message_id,
                uid=uid,
                subject=subject,
                sender=sender,
                recipients=recipients,
                cc=cc,
                bcc=bcc,
                date=date,
                body_text=text_body,
                body_html=html_body,
                attachments=attachments,
                in_reply_to=in_reply_to,
                references=references,
            )

        except Exception as e:
            logger.error(f"Failed to parse email UID {uid}: {e}")
            return None

    def select_folder(self, folder: str = "INBOX") -> int:
        """Select a mailbox folder. Returns message count."""
        if not self._connection:
            raise IMAPError("Not connected")
        
        status, data = self._connection.select(folder)
        if status != "OK":
            raise IMAPError(f"Failed to select folder {folder}")
        
        return int(data[0])

    def search(
        self,
        criteria: str = "ALL",
        folder: str = "INBOX"
    ) -> List[int]:
        """
        Search for emails matching criteria.
        
        Common criteria:
        - "ALL": All emails
        - "UNSEEN": Unread emails
        - "SEEN": Read emails
        - "FROM <addr>": From specific address
        - "SUBJECT <text>": Subject contains text
        - "SINCE <date>": Since date (DD-Mon-YYYY)
        """
        if not self._connection:
            raise IMAPError("Not connected")
        
        self.select_folder(folder)
        
        status, data = self._connection.search(None, criteria)
        if status != "OK":
            raise IMAPError(f"Search failed: {criteria}")
        
        uids = data[0].split()
        return [int(uid) for uid in uids]

    def fetch_emails(
        self,
        uids: List[int],
        mark_as_read: bool = False
    ) -> Generator[EmailMessage, None, None]:
        """Fetch emails by UIDs."""
        if not self._connection:
            raise IMAPError("Not connected")
        
        for uid in uids:
            try:
                # Fetch email
                status, data = self._connection.fetch(str(uid).encode(), "(RFC822)")
                if status != "OK":
                    logger.warning(f"Failed to fetch email UID {uid}")
                    continue
                
                raw_email = data[0][1]
                email_msg = self._parse_email(uid, raw_email)
                
                if email_msg:
                    if mark_as_read:
                        self.mark_as_read(uid)
                    yield email_msg
                    
            except Exception as e:
                logger.error(f"Error fetching email UID {uid}: {e}")

    def fetch_unread(
        self,
        folder: str = "INBOX",
        limit: Optional[int] = None,
        mark_as_read: bool = False
    ) -> List[EmailMessage]:
        """Fetch unread emails from folder."""
        uids = self.search("UNSEEN", folder)
        
        if limit:
            uids = uids[-limit:]  # Get most recent
        
        return list(self.fetch_emails(uids, mark_as_read))

    def fetch_all(
        self,
        folder: str = "INBOX",
        limit: Optional[int] = None
    ) -> List[EmailMessage]:
        """Fetch all emails from folder."""
        uids = self.search("ALL", folder)
        
        if limit:
            uids = uids[-limit:]
        
        return list(self.fetch_emails(uids))

    def mark_as_read(self, uid: int) -> bool:
        """Mark email as read."""
        if not self._connection:
            raise IMAPError("Not connected")
        
        status, _ = self._connection.store(str(uid).encode(), "+FLAGS", "\\Seen")
        return status == "OK"

    def mark_as_unread(self, uid: int) -> bool:
        """Mark email as unread."""
        if not self._connection:
            raise IMAPError("Not connected")
        
        status, _ = self._connection.store(str(uid).encode(), "-FLAGS", "\\Seen")
        return status == "OK"

    def move_to_folder(self, uid: int, destination: str) -> bool:
        """Move email to another folder."""
        if not self._connection:
            raise IMAPError("Not connected")
        
        # Copy to destination
        status, _ = self._connection.copy(str(uid).encode(), destination)
        if status != "OK":
            return False
        
        # Mark original as deleted
        self._connection.store(str(uid).encode(), "+FLAGS", "\\Deleted")
        self._connection.expunge()
        
        return True

    def get_folders(self) -> List[str]:
        """Get list of available folders."""
        if not self._connection:
            raise IMAPError("Not connected")
        
        status, folders = self._connection.list()
        if status != "OK":
            raise IMAPError("Failed to list folders")
        
        folder_names = []
        for folder in folders:
            if isinstance(folder, bytes):
                # Parse folder name from response
                parts = folder.decode().split(' "/" ')
                if len(parts) > 1:
                    folder_names.append(parts[-1].strip('"'))
        
        return folder_names
