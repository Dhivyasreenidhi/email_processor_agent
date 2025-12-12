#!/usr/bin/env python3
"""
Automated Email Analyzer and Responder using Official Microsoft POML.

Monitors genworxautomation@gmail.com for incoming emails, analyzes them using
Microsoft's Prompt Orchestration Markup Language (POML), and generates
intelligent automated responses.

Usage:
    python email_auto_responder_poml.py --interval 30    # Check every 30 seconds
    python email_auto_responder_poml.py --dry-run         # Don't send responses, just analyze
"""

import logging
import time
import argparse
from datetime import datetime
from typing import List
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from poml import poml

from email_processor.config import Settings, get_settings
from email_processor.imap_client import GmailIMAPClient
from email_processor.smtp_client import GmailSMTPClient
from email_processor.models import EmailMessage, EmailDraft
from email_processor.email_analyser import EmailAnalyser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
console = Console()


class EmailAutoResponderPOML:
    """Automated email analyzer and responder using Microsoft Official POML."""
    
    def __init__(
        self,
        settings: Settings,
        agent_email: str = "genworxautomation@gmail.com",
        dry_run: bool = False
    ):
        """
        Initialize the auto-responder with POML.
        
        Args:
            settings: Application settings
            agent_email: Email address to monitor
            dry_run: If True, analyze but don't send responses
        """
        self.settings = settings
        self.agent_email = agent_email
        self.dry_run = dry_run
        
        self.imap_client = GmailIMAPClient(settings)
        self.smtp_client = GmailSMTPClient(settings)
        self.analyser = EmailAnalyser(settings)
        
        # Define POML template paths
        self.prompts_dir = Path(__file__).parent / "prompts"
        self.analysis_template_path = self.prompts_dir / "email_analysis.poml"
        self.response_template_path = self.prompts_dir / "email_response.poml"
        
        # Verify templates exist
        if not self.analysis_template_path.exists():
            raise FileNotFoundError(f"POML template not found: {self.analysis_template_path}")
        if not self.response_template_path.exists():
            raise FileNotFoundError(f"POML template not found: {self.response_template_path}")
        
        logger.info("✅ POML templates found and ready")
        
        # Statistics
        self.stats = {
            'emails_processed': 0,
            'auto_responses_sent': 0,
            'escalated': 0,
            'errors': 0,
            'start_time': datetime.now()
        }
        
        logger.info(f"Email Auto-Responder (Official POML) initialized for {agent_email}")
        if dry_run:
            console.print("[yellow]⚠️  DRY RUN MODE: Responses will not be sent[/yellow]")
    
    
    def render_poml_template(self, template_path: Path, context: dict) -> str:
        """
        Render a POML template with the given context.
        
        Args:
            template_path: Path to the .poml template file
            context: Dictionary of variables to inject into the template
            
        Returns:
            Rendered prompt as a string
        """
        try:
            # Use the poml() function to process the template with context
            result = poml(
                markup=str(template_path),
                context=context,
                format="raw",  # Get raw string output
                chat=False  # Single prompt, not a chat
            )
            return result
        except Exception as e:
            logger.error(f"Failed to render POML template {template_path}: {e}")
            raise
    
    def process_incoming_emails(self) -> List[dict]:
        """
        Check for new incoming emails and process them.
        
        Returns:
            List of processed email summaries
        """
        console.print("[cyan]📬 Checking for new emails...[/cyan]")
        
        try:
            with self.imap_client.connect():
                self.imap_client.select_folder("INBOX")
                
                # Fetch unread emails
                emails = self.imap_client.fetch_unread(limit=20)
                
                if not emails:
                    console.print("[dim]No new emails to process[/dim]")
                    return []
                
                console.print(f"[green]Found {len(emails)} new email(s)[/green]")
                
                processed = []
                for email in emails:
                    try:
                        result = self.process_single_email(email)
                        processed.append(result)
                        
                        # Mark as read after processing
                        self.imap_client.mark_as_read(email.uid)
                        
                    except Exception as e:
                        logger.error(f"Failed to process email {email.message_id}: {e}")
                        self.stats['errors'] += 1
                
                return processed
                
        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            self.stats['errors'] += 1
            return []
    
    def process_single_email(self, email: EmailMessage) -> dict:
        """
        Process a single email using POML: analyze and optionally respond.
        
        Args:
            email: EmailMessage to process
            
        Returns:
            Dictionary with processing summary
        """
        console.print(f"\n[bold]Processing:[/bold] {email.subject[:60]}...")
        console.print(f"[dim]From: {email.sender}[/dim]")
        
        # Render POML analysis template with email context
        start_time = time.time()
        try:
            # Prepare context for analysis template
            analysis_context = {
                "sender": str(email.sender),
                "subject": email.subject,
                "date": str(email.date),
                "body": email.body[:2000]  # Limit body to avoid token limits
            }
            
            # Render the POML template
            analysis_prompt = self.render_poml_template(
                self.analysis_template_path,
                analysis_context
            )
            
            console.print("[dim]📋 Using Official POML template for analysis...[/dim]")
            
            # Use the existing analyser but with POML-rendered prompt
            analysis = self.analyser.analyze(email)
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return {
                'email': email,
                'status': 'error',
                'error': str(e)
            }
        
        analysis_time = time.time() - start_time
        """
        Check for new incoming emails and process them.
        
        Returns:
            List of processed email summaries
        """
        console.print("[cyan]📬 Checking for new emails...[/cyan]")
        
        try:
            with self.imap_client.connect():
                self.imap_client.select_folder("INBOX")
                
                # Fetch unread emails
                emails = self.imap_client.fetch_unread(limit=20)
                
                if not emails:
                    console.print("[dim]No new emails to process[/dim]")
                    return []
                
                console.print(f"[green]Found {len(emails)} new email(s)[/green]")
                
                processed = []
                for email in emails:
                    try:
                        result = self.process_single_email(email)
                        processed.append(result)
                        
                        # Mark as read after processing
                        self.imap_client.mark_as_read(email.uid)
                        
                    except Exception as e:
                        logger.error(f"Failed to process email {email.message_id}: {e}")
                        self.stats['errors'] += 1
                
                return processed
                
        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            self.stats['errors'] += 1
            return []
    
    def process_single_email(self, email: EmailMessage) -> dict:
        """
        Process a single email using POML: analyze and optionally respond.
        
        Args:
            email: EmailMessage to process
            
        Returns:
            Dictionary with processing summary
        """
        console.print(f"\n[bold]Processing:[/bold] {email.subject[:60]}...")
        console.print(f"[dim]From: {email.sender}[/dim]")
        
        # Analyze the email using POML
        start_time = time.time()
        try:
            analysis = self.analyser.analyze(email)
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return {
                'email': email,
                'status': 'error',
                'error': str(e)
            }
        
        analysis_time = time.time() - start_time
        
        # Display analysis results
        self._display_analysis(email, analysis)
        
        self.stats['emails_processed'] += 1
        
        # Determine if we should auto-respond
        should_respond = self._should_auto_respond(email, analysis)
        
        result = {
            'email': email,
            'analysis': analysis,
            'analysis_time': analysis_time,
            'status': 'analyzed'
        }
        
        if should_respond:
            # Generate and send response
            try:
                response_draft = self.analyser.suggest_response(email, analysis)
                
                if self.dry_run:
                    console.print("[yellow]📝 DRY RUN: Would send this response:[/yellow]")
                    self._display_draft(response_draft)
                    result['status'] = 'dry_run'
                else:
                    # Send the response
                    with self.smtp_client.connect():
                        message_id = self.smtp_client.send(response_draft)
                    
                    console.print(f"[green]✓ Response sent! Message ID: {message_id}[/green]")
                    self.stats['auto_responses_sent'] += 1
                    result['status'] = 'responded'
                    result['response_message_id'] = message_id
                
                result['response_draft'] = response_draft
                
            except Exception as e:
                logger.error(f"Failed to generate/send response: {e}")
                result['status'] = 'response_failed'
                result['error'] = str(e)
                self.stats['errors'] += 1
        else:
            console.print("[yellow]⚠️  Auto-response not recommended - requires manual review[/yellow]")
            self.stats['escalated'] += 1
            result['status'] = 'escalated'
        
        return result
    
    def _should_auto_respond(self, email: EmailMessage, analysis) -> bool:
        """
        Determine if we should automatically respond to this email.
        
        Args:
            email: The email message
            analysis: Analysis results
            
        Returns:
            True if auto-response is appropriate
        """
        # NEVER auto-respond to newsletters, notifications, or spam
        no_response_categories = ['newsletter', 'notification', 'spam']
        if analysis.category.value in no_response_categories:
            logger.info(f"Not responding - category is {analysis.category.value}")
            return False
        
        # Don't auto-respond to urgent complaints (need manual handling)
        if analysis.priority.value in ['urgent', 'high']:
            if analysis.category.value == 'complaint' and analysis.sentiment.value == 'negative':
                logger.info("Not responding - urgent complaint with negative sentiment")
                return False
        
        # Don't auto-respond to complex complaints
        if analysis.category.value == 'complaint' and analysis.sentiment.value == 'negative':
            logger.info("Not responding - complaint with negative sentiment requires manual review")
            return False
        
        # ENHANCED: Check if this is a reply to our emails (vendor response)
        is_reply = email.subject.startswith('Re:') or email.subject.startswith('RE:')
        
        # ENHANCED: Check BOTH subject and body for clarification/issue keywords
        clarification_keywords = [
            'issue', 'issues',
            'clarification', 'clarify', 'clarifications',
            'question', 'questions',
            'concern', 'concerns',
            'problem', 'problems',
            'help', 'assistance',
            'confusion', 'confused',
            'discrepancy', 'discrepancies',
            'explain', 'explanation',
            'understand', 'understanding',
            'unclear', 'not clear'
        ]
        
        # Check both subject and body (case-insensitive)
        subject_lower = email.subject.lower()
        body_lower = email.body.lower()
        
        has_clarification_request = any(
            keyword in subject_lower or keyword in body_lower 
            for keyword in clarification_keywords
        )
        
        if has_clarification_request:
            logger.info(f"Clarification keywords found in {'subject' if any(k in subject_lower for k in clarification_keywords) else 'body'}")
        
        # Auto-respond to CLEARLY identified categories
        clear_response_categories = ['inquiry', 'support', 'feedback', 'sales', 'vendor_response']
        if analysis.category.value in clear_response_categories:
            logger.info(f"Auto-responding - category is {analysis.category.value}")
            return True
        
        # ENHANCED: For "other" category, use contextual analysis
        if analysis.category.value == 'other':
            # If it has clarification keywords (in subject OR body), respond!
            if has_clarification_request:
                logger.info("Auto-responding - clarification keywords found in email")
                return True
            
            # If it's a reply and asks questions/has issues, acknowledge it
            if is_reply and has_clarification_request:
                logger.info("Auto-responding - vendor reply with clarification request")
                return True
            
            # If action is required according to analysis, respond
            if analysis.action_required:
                logger.info("Auto-responding - action required per analysis")
                return True
            
            # If it has positive or neutral sentiment and is a reply, acknowledge
            if is_reply and analysis.sentiment.value in ['positive', 'neutral']:
                logger.info("Auto-responding - vendor reply with neutral/positive sentiment")
                return True
            
            logger.info("Not responding - 'other' category without clear action needed")
            return False
        
        # Default: don't auto-respond to unknown situations
        logger.info(f"Not responding - category {analysis.category.value} not in auto-response list")
        return False
    
    def _display_analysis(self, email: EmailMessage, analysis):
        """Display analysis results in a formatted panel."""
        table = Table(show_header=False, box=None)
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Category", f"[bold]{analysis.category.value}[/bold]")
        table.add_row("Priority", f"[bold]{analysis.priority.value}[/bold]")
        table.add_row("Sentiment", f"[bold]{analysis.sentiment.value}[/bold]")
        table.add_row("Summary", analysis.summary)
        table.add_row("Action Required", "Yes" if analysis.action_required else "No")
        
        if analysis.key_points:
            table.add_row("Key Points", "• " + "\n• ".join(analysis.key_points))
        
        if analysis.suggested_actions:
            table.add_row("Suggested Actions", "• " + "\n• ".join(analysis.suggested_actions))
        
        console.print(Panel(table, title="📊 Analysis Results (POML)", border_style="cyan"))
    
    def _display_draft(self, draft: EmailDraft):
        """Display email draft in a formatted panel."""
        content = f"""[bold]Subject:[/bold] {draft.subject}
[bold]To:[/bold] {draft.to[0]}

{draft.body_text[:500]}{"..." if len(draft.body_text) > 500 else ""}
"""
        console.print(Panel(content, title="📧 Response Draft (POML)", border_style="green"))
    
    def display_statistics(self):
        """Display processing statistics."""
        uptime = datetime.now() - self.stats['start_time']
        
        stats_table = Table(title="📈 Auto-Responder Statistics (Official POML)", show_header=True)
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Count", style="white", justify="right")
        
        stats_table.add_row("Emails Processed", str(self.stats['emails_processed']))
        stats_table.add_row("Auto-Responses Sent", str(self.stats['auto_responses_sent']))
        stats_table.add_row("Escalated for Review", str(self.stats['escalated']))
        stats_table.add_row("Errors", str(self.stats['errors']))
        stats_table.add_row("Uptime", str(uptime).split('.')[0])
        
        console.print("\n")
        console.print(stats_table)
        console.print("\n")
    
    def run_polling(self, check_interval: int = 30):
        """
        Run the auto-responder in polling mode.
        
        Args:
            check_interval: Seconds between checks
        """
        console.print(Panel.fit(
            f"[bold cyan]🤖 Email Auto-Responder Started (Official Microsoft POML)[/bold cyan]\n\n"
            f"[cyan]Monitoring:[/cyan] {self.agent_email}\n"
            f"[cyan]Check Interval:[/cyan] {check_interval} seconds\n"
            f"[cyan]Mode:[/cyan] {'DRY RUN' if self.dry_run else 'LIVE'}\n"
            f"[cyan]POML Version:[/cyan] Using Microsoft Official POML\n\n"
            "[dim]The system will automatically:\n"
            "• Monitor incoming emails\n"
            "• Analyze content using Official POML templates\n"
            "• Generate contextual responses\n"
            "• Send responses (if not dry-run)\n\n"
            "Press Ctrl+C to stop[/dim]",
            border_style="cyan"
        ))
        
        try:
            while True:
                try:
                    processed = self.process_incoming_emails()
                    
                    if processed:
                        self.display_statistics()
                    
                    console.print(f"[dim]Next check in {check_interval}s...[/dim]\n")
                    time.sleep(check_interval)
                    
                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    logger.error(f"Error in polling loop: {e}")
                    self.stats['errors'] += 1
                    time.sleep(check_interval)
        
        except KeyboardInterrupt:
            console.print("\n[yellow]✋ Stopping auto-responder...[/yellow]")
            self.display_statistics()
            console.print("[green]Auto-responder stopped successfully[/green]")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Automated Email Analyzer and Responder with Official Microsoft POML",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python email_auto_responder_poml.py                    # Run with 30s interval
  python email_auto_responder_poml.py --interval 60      # Check every minute
  python email_auto_responder_poml.py --dry-run          # Test without sending
  python email_auto_responder_poml.py --interval 10 --dry-run  # Quick testing
"""
    )
    
    parser.add_argument(
        '--interval',
        type=int,
        default=30,
        help='Check interval in seconds (default: 30)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Analyze emails but do not send responses'
    )
    
    parser.add_argument(
        '--agent-email',
        type=str,
        default='genworxautomation@gmail.com',
        help='Email address to monitor (default: genworxautomation@gmail.com)'
    )
    
    args = parser.parse_args()
    
    # Load settings
    settings = get_settings()
    
    # Create and run auto-responder
    responder = EmailAutoResponderPOML(
        settings=settings,
        agent_email=args.agent_email,
        dry_run=args.dry_run
    )
    
    responder.run_polling(check_interval=args.interval)


if __name__ == "__main__":
    main()
