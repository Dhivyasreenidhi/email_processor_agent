"""
Email Approval Workflow System.

Implements an email approval workflow where:
1. Draft emails are sent to an approver (CFO) for review
2. The approver responds with APPROVED or REJECTED
3. Upon approval, the email is automatically sent to the final recipient
"""

import json
import logging
import time
import hashlib
from datetime import datetime
from typing import Optional, List, Callable
from pathlib import Path
from dataclasses import dataclass, field, asdict
from enum import Enum

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from email_processor.config import Settings
from email_processor.models import EmailMessage, EmailDraft, EmailAddress
from email_processor.imap_client import GmailIMAPClient
from email_processor.smtp_client import GmailSMTPClient

logger = logging.getLogger(__name__)
console = Console()


class ApprovalStatus(str, Enum):
    """Status of an approval request."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class ApprovalRequest:
    """Represents a pending approval request."""
    request_id: str
    draft: EmailDraft
    final_recipient: EmailAddress
    approver_email: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    approved_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    approval_message_id: Optional[str] = None
    notes: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "request_id": self.request_id,
            "draft_to": [str(a.email) for a in self.draft.to],
            "draft_subject": self.draft.subject,
            "draft_body": self.draft.body_text,
            "draft_body_html": self.draft.body_html,  # Include HTML body
            "final_recipient_email": self.final_recipient.email,
            "final_recipient_name": self.final_recipient.name,
            "approver_email": self.approver_email,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "rejected_at": self.rejected_at.isoformat() if self.rejected_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "approval_message_id": self.approval_message_id,
            "notes": self.notes,
        }


class ApprovalWorkflow:
    """
    Email Approval Workflow Manager.
    
    Manages the flow of:
    1. Sending draft emails to approver for review
    2. Monitoring for approval responses
    3. Sending approved emails to final recipients
    """

    APPROVAL_SUBJECT_PREFIX = "[APPROVAL REQUIRED]"
    APPROVED_KEYWORDS = ["approved", "approve", "yes", "ok", "go ahead", "confirmed", "confirm"]
    REJECTED_KEYWORDS = ["rejected", "reject", "no", "denied", "deny", "cancel"]

    def __init__(
        self,
        settings: Settings,
        approver_email: str,
        storage_path: Optional[Path] = None
    ):
        """
        Initialize the approval workflow.
        
        Args:
            settings: Application settings
            approver_email: Email of the approver (CFO)
            storage_path: Path to store pending approvals (default: ./pending_approvals.json)
        """
        self.settings = settings
        self.approver_email = approver_email
        self.storage_path = storage_path or Path("./pending_approvals.json")
        
        self.imap_client = GmailIMAPClient(settings)
        self.smtp_client = GmailSMTPClient(settings)
        
        # Load pending approvals
        self.pending_approvals: dict[str, ApprovalRequest] = {}
        self._load_pending_approvals()
        
        # Callbacks
        self._on_approved: List[Callable[[ApprovalRequest], None]] = []
        self._on_rejected: List[Callable[[ApprovalRequest], None]] = []
        self._on_sent: List[Callable[[ApprovalRequest], None]] = []
        
        logger.info(f"Approval Workflow initialized. Approver: {approver_email}")

    def _generate_request_id(self, draft: EmailDraft) -> str:
        """Generate a unique request ID."""
        content = f"{draft.subject}{draft.body_text}{datetime.now().isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()[:12].upper()

    def _load_pending_approvals(self):
        """Load pending approvals from storage."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    for item in data:
                        # Reconstruct ApprovalRequest from dict
                        draft = EmailDraft(
                            to=[EmailAddress(email=item["draft_to"][0])],
                            subject=item["draft_subject"],
                            body_text=item["draft_body"]
                        )
                        final_recipient = EmailAddress(
                            email=item["final_recipient_email"],
                            name=item.get("final_recipient_name")
                        )
                        request = ApprovalRequest(
                            request_id=item["request_id"],
                            draft=draft,
                            final_recipient=final_recipient,
                            approver_email=item["approver_email"],
                            status=ApprovalStatus(item["status"]),
                            created_at=datetime.fromisoformat(item["created_at"]),
                            approval_message_id=item.get("approval_message_id"),
                            notes=item.get("notes"),
                        )
                        if item.get("approved_at"):
                            request.approved_at = datetime.fromisoformat(item["approved_at"])
                        if item.get("rejected_at"):
                            request.rejected_at = datetime.fromisoformat(item["rejected_at"])
                        if item.get("sent_at"):
                            request.sent_at = datetime.fromisoformat(item["sent_at"])
                        
                        if request.status == ApprovalStatus.PENDING:
                            self.pending_approvals[request.request_id] = request
                            
                logger.info(f"Loaded {len(self.pending_approvals)} pending approvals")
            except Exception as e:
                logger.warning(f"Failed to load pending approvals: {e}")

    def _save_pending_approvals(self):
        """Save pending approvals to storage."""
        try:
            data = [req.to_dict() for req in self.pending_approvals.values()]
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save pending approvals: {e}")

    def _create_approval_email(self, request: ApprovalRequest) -> EmailDraft:
        """Create the approval request email to send to approver."""
        body = f"""
Dear CFO,

An email requires your approval before being sent.

═══════════════════════════════════════════════════════════════
📧 APPROVAL REQUEST ID: {request.request_id}
═══════════════════════════════════════════════════════════════

FINAL RECIPIENT: {request.final_recipient.name or ''} <{request.final_recipient.email}>

SUBJECT: {request.draft.subject}

EMAIL CONTENT:
───────────────────────────────────────────────────────────────
{request.draft.body_text}
───────────────────────────────────────────────────────────────

═══════════════════════════════════════════════════════════════
HOW TO RESPOND:
═══════════════════════════════════════════════════════════════

To APPROVE this email, reply with: APPROVED
To REJECT this email, reply with: REJECTED

You can also add notes after your decision.
Example: "APPROVED - looks good" or "REJECTED - needs revision"

═══════════════════════════════════════════════════════════════

This approval request was generated automatically.
Request ID: {request.request_id}
Created: {request.created_at.strftime('%Y-%m-%d %H:%M:%S')}

Best regards,
Email Processor Agent
"""
        
        return EmailDraft(
            to=[EmailAddress(email=request.approver_email)],
            subject=f"{self.APPROVAL_SUBJECT_PREFIX} {request.draft.subject} [ID: {request.request_id}]",
            body_text=body.strip(),
        )

    def submit_for_approval(
        self,
        draft: EmailDraft,
        final_recipient_email: str,
        final_recipient_name: Optional[str] = None
    ) -> ApprovalRequest:
        """
        Submit an email draft for approval.
        
        Args:
            draft: The email draft to be approved
            final_recipient_email: The actual recipient once approved
            final_recipient_name: Optional name of the final recipient
            
        Returns:
            ApprovalRequest with tracking information
        """
        console.print(Panel.fit(
            f"[bold cyan]📋 Submitting Email for Approval[/bold cyan]\n"
            f"Approver: {self.approver_email}\n"
            f"Final Recipient: {final_recipient_email}",
            border_style="cyan"
        ))

        # Create approval request
        final_recipient = EmailAddress(
            email=final_recipient_email,
            name=final_recipient_name
        )
        
        request = ApprovalRequest(
            request_id=self._generate_request_id(draft),
            draft=draft,
            final_recipient=final_recipient,
            approver_email=self.approver_email,
        )

        # Send approval request email
        approval_email = self._create_approval_email(request)
        
        with self.smtp_client.connect():
            message_id = self.smtp_client.send(approval_email)
            request.approval_message_id = message_id

        # Store the pending approval
        self.pending_approvals[request.request_id] = request
        self._save_pending_approvals()

        console.print(f"[green]✓ Approval request sent![/green]")
        console.print(f"  Request ID: [bold]{request.request_id}[/bold]")
        console.print(f"  Waiting for approval from: {self.approver_email}")

        return request

    def _parse_approval_response(self, email: EmailMessage) -> tuple[Optional[str], ApprovalStatus, Optional[str]]:
        """
        Parse an email to check if it's an approval response.
        
        Returns:
            Tuple of (request_id, status, notes) or (None, None, None) if not an approval response
        """
        subject = email.subject.upper()
        body = email.body.strip().upper()
        
        # Check if this is a response to an approval request
        if "RE:" not in subject.upper() and self.APPROVAL_SUBJECT_PREFIX.upper() not in subject.upper():
            return None, ApprovalStatus.PENDING, None
        
        # Try to extract request ID from subject
        request_id = None
        if "[ID:" in subject:
            try:
                start = subject.index("[ID:") + 4
                end = subject.index("]", start)
                request_id = subject[start:end].strip()
            except ValueError:
                pass
        
        # If no ID in subject, try to find a pending request
        if not request_id:
            # Check if it's from the approver
            if email.sender.email.lower() != self.approver_email.lower():
                return None, ApprovalStatus.PENDING, None
            
            # Find the most recent pending request
            if self.pending_approvals:
                request_id = list(self.pending_approvals.keys())[-1]
        
        if not request_id or request_id not in self.pending_approvals:
            return None, ApprovalStatus.PENDING, None
        
        # Parse the response
        body_lower = email.body.strip().lower()
        first_line = body_lower.split('\n')[0].strip()
        
        # Check for approval
        for keyword in self.APPROVED_KEYWORDS:
            if keyword in first_line:
                notes = email.body.strip()
                return request_id, ApprovalStatus.APPROVED, notes
        
        # Check for rejection
        for keyword in self.REJECTED_KEYWORDS:
            if keyword in first_line:
                notes = email.body.strip()
                return request_id, ApprovalStatus.REJECTED, notes
        
        return request_id, ApprovalStatus.PENDING, None

    def _send_final_email(self, request: ApprovalRequest):
        """Send the approved email to the final recipient."""
        # Create the final email with the actual recipient
        final_email = EmailDraft(
            to=[request.final_recipient],
            subject=request.draft.subject,
            body_text=request.draft.body_text,
            body_html=request.draft.body_html,
        )

        console.print(f"[cyan]📤 Sending approved email to {request.final_recipient.email}...[/cyan]")
        
        with self.smtp_client.connect():
            message_id = self.smtp_client.send(final_email)
        
        request.sent_at = datetime.now()
        self._save_pending_approvals()

        console.print(f"[green]✓ Email sent to {request.final_recipient.email}![/green]")
        
        # Notify callbacks
        for callback in self._on_sent:
            try:
                callback(request)
            except Exception as e:
                logger.error(f"Callback error: {e}")

        return message_id

    def check_approvals(self) -> List[ApprovalRequest]:
        """
        Check for approval responses and process them.
        
        Returns:
            List of processed approval requests
        """
        if not self.pending_approvals:
            console.print("[yellow]No pending approvals to check[/yellow]")
            return []

        console.print(f"[cyan]🔍 Checking for approval responses...[/cyan]")
        console.print(f"   Pending approvals: {len(self.pending_approvals)}")

        processed = []

        # FIRST: Check the JSON file for UI-based status changes
        # (Rejections/Approvals made through the web UI)
        try:
            if self.storage_path.exists():
                with open(self.storage_path, 'r') as f:
                    all_approvals = json.load(f)
                
                for item in all_approvals:
                    request_id = item['request_id']
                    
                    # Check if this was a pending request that changed status via UI
                    if request_id in self.pending_approvals:
                        request = self.pending_approvals[request_id]
                        new_status = item.get('status')
                        
                        # Handle UI-based REJECTION
                        if new_status == 'rejected':
                            console.print(Panel.fit(
                                f"[bold red]✗ REJECTED (via UI)[/bold red]\n"
                                f"Request ID: {request_id}\n"
                                f"Subject: {request.draft.subject}\n"
                                f"Notes: {item.get('notes', 'No reason provided')}",
                                border_style="red"
                            ))
                            
                            request.status = ApprovalStatus.REJECTED
                            request.rejected_at = datetime.now()
                            request.notes = item.get('notes', 'Rejected via web UI')
                            
                            # Remove from pending
                            del self.pending_approvals[request_id]
                            
                            processed.append(request)
                            
                            # Notify callbacks
                            for callback in self._on_rejected:
                                try:
                                    callback(request)
                                except Exception as e:
                                    logger.error(f"Callback error: {e}")
                        
                        # Handle UI-based APPROVAL
                        elif new_status == 'approved' and item.get('sent_at'):
                            console.print(Panel.fit(
                                f"[bold green]✓ APPROVED (via UI)[/bold green]\n"
                                f"Request ID: {request_id}\n"
                                f"Subject: {request.draft.subject}",
                                border_style="green"
                            ))
                            
                            request.status = ApprovalStatus.APPROVED
                            request.approved_at = datetime.now()
                            request.notes = item.get('notes', 'Approved via web UI')
                            
                            # Remove from pending
                            del self.pending_approvals[request_id]
                            
                            processed.append(request)
                            
                            # Notify callbacks
                            for callback in self._on_approved:
                                try:
                                    callback(request)
                                except Exception as e:
                                    logger.error(f"Callback error: {e}")
        
        except Exception as e:
            logger.error(f"Error checking UI-based status changes: {e}")

        # SECOND: Check for email-based approval responses
        with self.imap_client.connect():
            # Search for emails from the approver
            self.imap_client.select_folder("INBOX")
            
            # Get unread emails
            emails = self.imap_client.fetch_unread(limit=20)
            
            for email in emails:
                # Check if from approver
                if email.sender.email.lower() != self.approver_email.lower():
                    continue
                
                request_id, status, notes = self._parse_approval_response(email)
                
                if not request_id or request_id not in self.pending_approvals:
                    continue
                
                request = self.pending_approvals[request_id]
                
                if status == ApprovalStatus.APPROVED:
                    console.print(Panel.fit(
                        f"[bold green]✓ APPROVED (via Email)[/bold green]\n"
                        f"Request ID: {request_id}\n"
                        f"Subject: {request.draft.subject}",
                        border_style="green"
                    ))
                    
                    request.status = ApprovalStatus.APPROVED
                    request.approved_at = datetime.now()
                    request.notes = notes
                    
                    # Send the final email
                    self._send_final_email(request)
                    
                    # Remove from pending
                    del self.pending_approvals[request_id]
                    self._save_pending_approvals()
                    
                    processed.append(request)
                    
                    # Mark approval email as read
                    self.imap_client.mark_as_read(email.uid)
                    
                    # Notify callbacks
                    for callback in self._on_approved:
                        try:
                            callback(request)
                        except Exception as e:
                            logger.error(f"Callback error: {e}")

                elif status == ApprovalStatus.REJECTED:
                    console.print(Panel.fit(
                        f"[bold red]✗ REJECTED (via Email)[/bold red]\n"
                        f"Request ID: {request_id}\n"
                        f"Subject: {request.draft.subject}\n"
                        f"Notes: {notes}",
                        border_style="red"
                    ))
                    
                    request.status = ApprovalStatus.REJECTED
                    request.rejected_at = datetime.now()
                    request.notes = notes
                    
                    # Remove from pending
                    del self.pending_approvals[request_id]
                    self._save_pending_approvals()
                    
                    processed.append(request)
                    
                    # Mark as read
                    self.imap_client.mark_as_read(email.uid)
                    
                    # Notify callbacks
                    for callback in self._on_rejected:
                        try:
                            callback(request)
                        except Exception as e:
                            logger.error(f"Callback error: {e}")

        return processed

    def run_polling(self, check_interval: int = 30):
        """
        Run the approval checker in polling mode.
        
        Args:
            check_interval: Seconds between checks
        """
        console.print(Panel.fit(
            f"[bold cyan]🔄 Approval Workflow Polling Started[/bold cyan]\n"
            f"Checking every {check_interval} seconds\n"
            f"Approver: {self.approver_email}\n"
            f"[dim]Press Ctrl+C to stop[/dim]",
            border_style="cyan"
        ))

        try:
            while True:
                processed = self.check_approvals()
                
                if processed:
                    console.print(f"[green]Processed {len(processed)} approval(s)[/green]")
                
                console.print(f"[dim]Next check in {check_interval}s...[/dim]")
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            console.print("\n[yellow]Polling stopped[/yellow]")

    def list_pending(self):
        """Display list of pending approvals."""
        if not self.pending_approvals:
            console.print("[yellow]No pending approvals[/yellow]")
            return

        table = Table(title="Pending Approvals", show_header=True)
        table.add_column("ID", style="cyan")
        table.add_column("Subject", style="white", max_width=40)
        table.add_column("Final Recipient", style="green")
        table.add_column("Created", style="yellow")
        table.add_column("Status", style="magenta")

        for request in self.pending_approvals.values():
            table.add_row(
                request.request_id,
                request.draft.subject[:40],
                request.final_recipient.email,
                request.created_at.strftime("%Y-%m-%d %H:%M"),
                request.status.value
            )

        console.print(table)

    # Event callbacks
    def on_approved(self, callback: Callable[[ApprovalRequest], None]):
        """Register callback for approval events."""
        self._on_approved.append(callback)
        return callback

    def on_rejected(self, callback: Callable[[ApprovalRequest], None]):
        """Register callback for rejection events."""
        self._on_rejected.append(callback)
        return callback

    def on_sent(self, callback: Callable[[ApprovalRequest], None]):
        """Register callback for sent events."""
        self._on_sent.append(callback)
        return callback
