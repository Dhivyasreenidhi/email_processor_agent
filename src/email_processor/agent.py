"""
Email Processor Agent - Main orchestrator.

Combines IMAP client, SMTP client, Email Generator, and Email Analyser
to provide a complete email processing solution.
"""

import logging
import time
from typing import Optional, List, Callable, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from email_processor.config import Settings, get_settings
from email_processor.models import (
    EmailMessage,
    EmailDraft,
    EmailAnalysis,
    EmailAddress,
    GenerationRequest,
    ResponseRequest,
    EmailCategory,
    EmailPriority,
)
from email_processor.imap_client import GmailIMAPClient
from email_processor.smtp_client import GmailSMTPClient
from email_processor.email_generator import EmailGenerator
from email_processor.email_analyser import EmailAnalyser


logger = logging.getLogger(__name__)
console = Console()


@dataclass
class ProcessingResult:
    """Result of processing an email."""
    email: EmailMessage
    analysis: Optional[EmailAnalysis] = None
    response_draft: Optional[EmailDraft] = None
    response_sent: bool = False
    error: Optional[str] = None


@dataclass
class AgentStats:
    """Statistics for the agent's operations."""
    emails_fetched: int = 0
    emails_analyzed: int = 0
    responses_generated: int = 0
    responses_sent: int = 0
    drafts_generated: int = 0
    errors: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    
    @property
    def uptime(self) -> timedelta:
        return datetime.now() - self.start_time


class EmailProcessorAgent:
    """
    Main Email Processor Agent.
    
    Orchestrates:
    - Email fetching via IMAP
    - Email analysis using AI
    - Response generation using AI
    - Email draft generation
    - Email sending via SMTP
    
    Can run in:
    - Interactive mode: Process on demand
    - Polling mode: Continuously monitor inbox
    """

    def __init__(self, settings: Optional[Settings] = None):
        """Initialize the Email Processor Agent."""
        self.settings = settings or get_settings()
        
        # Initialize clients
        self.imap_client = GmailIMAPClient(self.settings)
        self.smtp_client = GmailSMTPClient(self.settings)
        
        # Initialize AI processors
        self.generator = EmailGenerator(self.settings)
        self.analyser = EmailAnalyser(self.settings)
        
        # Statistics
        self.stats = AgentStats()
        
        # Callbacks for extensibility
        self._on_email_received: List[Callable[[EmailMessage], None]] = []
        self._on_email_analyzed: List[Callable[[EmailMessage, EmailAnalysis], None]] = []
        self._on_response_generated: List[Callable[[EmailMessage, EmailDraft], None]] = []
        
        logger.info("Email Processor Agent initialized")

    # =========================================================================
    # Event Callbacks
    # =========================================================================

    def on_email_received(self, callback: Callable[[EmailMessage], None]):
        """Register callback for when an email is received."""
        self._on_email_received.append(callback)
        return callback

    def on_email_analyzed(self, callback: Callable[[EmailMessage, EmailAnalysis], None]):
        """Register callback for when an email is analyzed."""
        self._on_email_analyzed.append(callback)
        return callback

    def on_response_generated(self, callback: Callable[[EmailMessage, EmailDraft], None]):
        """Register callback for when a response is generated."""
        self._on_response_generated.append(callback)
        return callback

    # =========================================================================
    # Email Fetching
    # =========================================================================

    def fetch_unread_emails(
        self,
        folder: str = "INBOX",
        limit: Optional[int] = None,
        mark_as_read: bool = False
    ) -> List[EmailMessage]:
        """Fetch unread emails from the inbox."""
        console.print(f"[cyan]📥 Fetching unread emails from {folder}...[/cyan]")
        
        with self.imap_client.connect():
            emails = self.imap_client.fetch_unread(
                folder=folder,
                limit=limit or self.settings.max_emails_per_batch,
                mark_as_read=mark_as_read
            )
        
        self.stats.emails_fetched += len(emails)
        
        for email in emails:
            for callback in self._on_email_received:
                try:
                    callback(email)
                except Exception as e:
                    logger.error(f"Callback error: {e}")
        
        console.print(f"[green]✓ Fetched {len(emails)} unread emails[/green]")
        return emails

    def fetch_recent_emails(
        self,
        folder: str = "INBOX",
        limit: int = 10
    ) -> List[EmailMessage]:
        """Fetch recent emails from the inbox."""
        console.print(f"[cyan]📥 Fetching {limit} recent emails from {folder}...[/cyan]")
        
        with self.imap_client.connect():
            emails = self.imap_client.fetch_all(folder=folder, limit=limit)
        
        self.stats.emails_fetched += len(emails)
        console.print(f"[green]✓ Fetched {len(emails)} emails[/green]")
        return emails

    # =========================================================================
    # Email Analysis
    # =========================================================================

    def analyze_email(self, email: EmailMessage) -> EmailAnalysis:
        """Analyze a single email."""
        console.print(f"[cyan]🔍 Analyzing: {email.subject[:50]}...[/cyan]")
        
        analysis = self.analyser.analyze(email)
        self.stats.emails_analyzed += 1
        
        for callback in self._on_email_analyzed:
            try:
                callback(email, analysis)
            except Exception as e:
                logger.error(f"Callback error: {e}")
        
        return analysis

    def analyze_emails(self, emails: List[EmailMessage]) -> List[EmailAnalysis]:
        """Analyze multiple emails."""
        results = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(
                f"Analyzing {len(emails)} emails...",
                total=len(emails)
            )
            
            for email in emails:
                try:
                    analysis = self.analyze_email(email)
                    results.append(analysis)
                except Exception as e:
                    logger.error(f"Analysis failed for {email.message_id}: {e}")
                    self.stats.errors += 1
                finally:
                    progress.advance(task)
        
        return results

    # =========================================================================
    # Response Generation
    # =========================================================================

    def generate_response(
        self,
        email: EmailMessage,
        intent: str,
        tone: str = "professional",
        additional_context: Optional[str] = None
    ) -> EmailDraft:
        """Generate a response to an email."""
        console.print(f"[cyan]✍️ Generating response to: {email.subject[:50]}...[/cyan]")
        
        request = ResponseRequest(
            original_email=email,
            response_intent=intent,
            tone=tone,
            include_original=True,
            additional_context=additional_context
        )
        
        draft = self.analyser.generate_response(request)
        self.stats.responses_generated += 1
        
        for callback in self._on_response_generated:
            try:
                callback(email, draft)
            except Exception as e:
                logger.error(f"Callback error: {e}")
        
        return draft

    def suggest_response(
        self,
        email: EmailMessage,
        analysis: Optional[EmailAnalysis] = None
    ) -> EmailDraft:
        """Automatically suggest a response based on analysis."""
        console.print(f"[cyan]💡 Suggesting response for: {email.subject[:50]}...[/cyan]")
        
        draft = self.analyser.suggest_response(email, analysis)
        self.stats.responses_generated += 1
        
        return draft

    # =========================================================================
    # Email Generation
    # =========================================================================

    def generate_email(
        self,
        purpose: str,
        recipient_email: str,
        recipient_name: Optional[str] = None,
        tone: str = "professional",
        key_points: Optional[List[str]] = None,
        signature_name: Optional[str] = None
    ) -> EmailDraft:
        """Generate a new email draft."""
        console.print(f"[cyan]✍️ Generating email: {purpose[:50]}...[/cyan]")
        
        request = GenerationRequest(
            purpose=purpose,
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            tone=tone,
            key_points=key_points or [],
            signature_name=signature_name,
            include_signature=True
        )
        
        draft = self.generator.generate(request)
        self.stats.drafts_generated += 1
        
        console.print(f"[green]✓ Generated email: {draft.subject}[/green]")
        return draft

    def generate_follow_up(
        self,
        original_subject: str,
        original_context: str,
        recipient_email: str,
        recipient_name: Optional[str] = None,
        days_since: int = 7,
        signature_name: Optional[str] = None
    ) -> EmailDraft:
        """Generate a follow-up email."""
        console.print(f"[cyan]✍️ Generating follow-up for: {original_subject[:50]}...[/cyan]")
        
        draft = self.generator.generate_follow_up(
            original_subject=original_subject,
            original_context=original_context,
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            days_since=days_since,
            signature_name=signature_name
        )
        
        self.stats.drafts_generated += 1
        return draft

    # =========================================================================
    # Email Sending
    # =========================================================================

    def send_email(self, draft: EmailDraft) -> str:
        """Send an email from draft."""
        console.print(f"[cyan]📤 Sending: {draft.subject}...[/cyan]")
        
        with self.smtp_client.connect():
            message_id = self.smtp_client.send(draft)
        
        self.stats.responses_sent += 1
        console.print(f"[green]✓ Email sent: {message_id}[/green]")
        
        return message_id

    # =========================================================================
    # Full Processing Pipeline
    # =========================================================================

    def process_email(
        self,
        email: EmailMessage,
        auto_respond: bool = False
    ) -> ProcessingResult:
        """
        Process a single email through the full pipeline.
        
        1. Analyze the email
        2. Generate response if action required
        3. Optionally send the response
        """
        result = ProcessingResult(email=email)
        
        try:
            # Analyze
            result.analysis = self.analyze_email(email)
            
            # Generate response if action required
            if result.analysis.action_required:
                result.response_draft = self.suggest_response(email, result.analysis)
                
                # Auto-send if configured
                if auto_respond and self.settings.auto_respond:
                    self.send_email(result.response_draft)
                    result.response_sent = True
                    
        except Exception as e:
            result.error = str(e)
            self.stats.errors += 1
            logger.error(f"Processing failed: {e}")
        
        return result

    def process_inbox(
        self,
        auto_respond: bool = False,
        limit: Optional[int] = None
    ) -> List[ProcessingResult]:
        """
        Process all unread emails in the inbox.
        
        Returns list of processing results.
        """
        console.print(Panel.fit(
            "[bold cyan]📧 Processing Inbox[/bold cyan]",
            border_style="cyan"
        ))
        
        # Fetch unread emails
        emails = self.fetch_unread_emails(limit=limit, mark_as_read=True)
        
        if not emails:
            console.print("[yellow]No unread emails to process[/yellow]")
            return []
        
        # Process each email
        results = []
        for email in emails:
            result = self.process_email(email, auto_respond)
            results.append(result)
        
        # Print summary
        self._print_processing_summary(results)
        
        return results

    def _print_processing_summary(self, results: List[ProcessingResult]):
        """Print a summary table of processing results."""
        table = Table(title="Processing Summary", show_header=True)
        table.add_column("Subject", style="cyan", max_width=40)
        table.add_column("Category", style="magenta")
        table.add_column("Priority", style="yellow")
        table.add_column("Sentiment", style="green")
        table.add_column("Action", style="blue")
        table.add_column("Response", style="white")
        
        for result in results:
            if result.analysis:
                action = "✓" if result.analysis.action_required else "-"
                response = "Sent" if result.response_sent else ("Draft" if result.response_draft else "-")
                
                table.add_row(
                    result.email.subject[:40],
                    result.analysis.category.value,
                    result.analysis.priority.value,
                    result.analysis.sentiment.value,
                    action,
                    response
                )
            else:
                table.add_row(
                    result.email.subject[:40],
                    "[red]Error[/red]",
                    "-",
                    "-",
                    "-",
                    result.error or "Unknown"
                )
        
        console.print(table)

    # =========================================================================
    # Polling Mode
    # =========================================================================

    def run_polling(
        self,
        auto_respond: bool = False,
        on_result: Optional[Callable[[ProcessingResult], None]] = None
    ):
        """
        Run the agent in polling mode.
        
        Continuously monitors the inbox and processes new emails.
        Press Ctrl+C to stop.
        """
        console.print(Panel.fit(
            f"[bold cyan]🤖 Email Processor Agent Started[/bold cyan]\n"
            f"Polling interval: {self.settings.poll_interval_seconds}s\n"
            f"Auto-respond: {'[green]ON[/green]' if auto_respond else '[red]OFF[/red]'}\n"
            f"[dim]Press Ctrl+C to stop[/dim]",
            border_style="cyan"
        ))
        
        try:
            while True:
                try:
                    # Process inbox
                    results = self.process_inbox(auto_respond=auto_respond)
                    
                    # Notify callback
                    if on_result:
                        for result in results:
                            on_result(result)
                    
                except Exception as e:
                    logger.error(f"Polling cycle error: {e}")
                    console.print(f"[red]Error during polling: {e}[/red]")
                
                # Wait for next poll
                console.print(f"[dim]Next check in {self.settings.poll_interval_seconds}s...[/dim]")
                time.sleep(self.settings.poll_interval_seconds)
                
        except KeyboardInterrupt:
            console.print("\n[yellow]Agent stopped by user[/yellow]")
            self._print_stats()

    # =========================================================================
    # Utilities
    # =========================================================================

    def _print_stats(self):
        """Print agent statistics."""
        table = Table(title="Agent Statistics", show_header=False)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Uptime", str(self.stats.uptime))
        table.add_row("Emails Fetched", str(self.stats.emails_fetched))
        table.add_row("Emails Analyzed", str(self.stats.emails_analyzed))
        table.add_row("Responses Generated", str(self.stats.responses_generated))
        table.add_row("Emails Sent", str(self.stats.responses_sent))
        table.add_row("Drafts Generated", str(self.stats.drafts_generated))
        table.add_row("Errors", str(self.stats.errors))
        
        console.print(table)

    def display_email(self, email: EmailMessage):
        """Display an email in a formatted panel."""
        console.print(Panel(
            f"[bold]From:[/bold] {email.sender}\n"
            f"[bold]To:[/bold] {', '.join(str(r) for r in email.recipients)}\n"
            f"[bold]Subject:[/bold] {email.subject}\n"
            f"[bold]Date:[/bold] {email.date.strftime('%Y-%m-%d %H:%M')}\n"
            f"[bold]Attachments:[/bold] {len(email.attachments)}\n"
            f"\n{email.body[:500]}{'...' if len(email.body) > 500 else ''}",
            title="📧 Email",
            border_style="cyan"
        ))

    def display_analysis(self, analysis: EmailAnalysis):
        """Display email analysis in a formatted panel."""
        console.print(Panel(
            f"[bold]Category:[/bold] {analysis.category.value}\n"
            f"[bold]Priority:[/bold] {analysis.priority.value}\n"
            f"[bold]Sentiment:[/bold] {analysis.sentiment.value}\n"
            f"[bold]Summary:[/bold] {analysis.summary}\n"
            f"[bold]Key Points:[/bold]\n{''.join(f'  • {p}\n' for p in analysis.key_points)}"
            f"[bold]Action Required:[/bold] {'Yes' if analysis.action_required else 'No'}\n"
            f"[bold]Suggested Actions:[/bold]\n{''.join(f'  • {a}\n' for a in analysis.suggested_actions)}"
            f"[bold]Confidence:[/bold] {analysis.confidence_score:.2%}",
            title="🔍 Analysis",
            border_style="green"
        ))

    def display_draft(self, draft: EmailDraft):
        """Display an email draft in a formatted panel."""
        console.print(Panel(
            f"[bold]To:[/bold] {', '.join(str(r) for r in draft.to)}\n"
            f"[bold]Subject:[/bold] {draft.subject}\n"
            f"[bold]Priority:[/bold] {draft.priority.value}\n"
            f"[bold]Is Reply:[/bold] {'Yes' if draft.is_reply else 'No'}\n"
            f"\n{draft.body_text}",
            title="✍️ Draft",
            border_style="yellow"
        ))
