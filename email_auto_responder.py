#!/usr/bin/env python3
"""
Automated Email Analyzer and Responder using POML System Prompts.

Monitors genworxautomation@gmail.com for incoming emails, analyzes them using
Process-Oriented Markup Language (POML) structured prompts, and generates
intelligent automated responses.

Usage:
    python email_auto_responder.py --interval 30    # Check every 30 seconds
    python email_auto_responder.py --dry-run         # Don't send responses, just analyze
"""

import logging
import time
import argparse
from datetime import datetime, timedelta
from typing import List, Optional
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from email_processor.config import Settings, get_settings
from email_processor.imap_client import GmailIMAPClient
from email_processor.smtp_client import GmailSMTPClient
from email_processor.models import EmailMessage, EmailDraft, EmailAddress
from email_processor.email_analyser import EmailAnalyser

# Guardrails AI for response validation
from email_guardrails import validate_email_response, quick_safety_check

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
console = Console()

# POML-Enhanced System Prompts
POML_ANALYSIS_PROMPT = """<|SYSTEM|>
You are an AI Email Analysis Agent using Process-Oriented Markup Language (POML) for structured email processing.

<|OBJECTIVE|>
Analyze incoming emails to genworxautomation@gmail.com and provide comprehensive structured analysis for automated response generation.

<|PROCESS|>
1. **Email Classification**:
   - Identify email type:
     * inquiry: Questions or requests for information (including clarification requests)
     * complaint: Customer complaints or issues
     * feedback: Feedback, reviews, or acknowledgments
     * support: Technical support requests or problem reports
     * sales: Sales inquiries or business development
     * partnership: Partnership or collaboration proposals
     * notification: Automated notifications or system messages
     * spam: Unwanted or promotional emails
     * vendor_response: Replies from vendors to our communications (often about invoices/discrepancies)
     * other: Emails that don't clearly fit other categories
   - Determine urgency: urgent, high, normal, low
   - Assess sentiment: positive, neutral, negative, mixed

2. **Content Extraction**:
   - Extract sender information (name, email, organization)
   - Identify primary intent and secondary intents
   - Extract key entities (products, services, dates, amounts, invoice numbers, PO numbers)
   - Identify action items and deadlines
   - Detect clarification or issue keywords (issue, problem, question, concern, clarification needed)

3. **Context Analysis**:
   - Check if subject starts with "Re:" or "RE:" (reply email)
   - Identify if this is a response to our previous communication
   - Identify referenced documents or previous communications
   - Assess business impact and priority

4. **Response Strategy**:
   - For vendor responses about invoices/discrepancies: ALWAYS recommend auto-response with acknowledgment
   - For clarification requests: Recommend auto-response
   - For simple inquiries: Recommend auto-response
   - For complaints: Recommend manual review
   - Determine required information for response
   - Suggest response approach and tone

<|SPECIAL_RULES|>
- If email subject contains "Re:" and mentions invoice/PO/discrepancy, categorize as "vendor_response" or "support"
- If email contains "issue", "clarification", "question", set action_required to true
- Vendor responses deserve acknowledgment even if categorized as "other"

<|OUTPUT_FORMAT|>
Respond with valid JSON following this structure:
{
  "classification": {
    "type": "inquiry|complaint|feedback|support|sales|partnership|notification|spam|vendor_response|other",
    "urgency": "urgent|high|normal|low",
    "sentiment": "positive|neutral|negative|mixed"
  },
  "content": {
    "primary_intent": "string - main purpose of email",
    "secondary_intents": ["string array - other purposes"],
    "key_entities": {
      "people": ["names"],
      "organizations": ["company names"],
      "products": ["product names"],
      "invoice_numbers": ["invoice numbers if mentioned"],
      "po_numbers": ["PO numbers if mentioned"],
      "dates": ["important dates"],
      "amounts": ["monetary amounts or quantities"]
    },
    "action_items": ["required actions"],
    "deadlines": ["any mentioned deadlines"],
    "has_clarification_request": boolean
  },
  "context": {
    "is_reply": boolean,
    "is_vendor_response": boolean,
    "references": ["referenced items"],
    "business_impact": "high|medium|low"
  },
  "response_strategy": {
    "should_auto_respond": boolean,
    "response_type": "acknowledge|answer|escalate|defer|reject",
    "recommended_tone": "professional|friendly|formal|empathetic|enthusiastic",
    "required_info": ["information needed for response"],
    "suggested_actions": ["actions to include in response"]
  },
  "summary": "2-3 sentence summary of the email",
  "confidence": 0.0-1.0
}
</|SYSTEM|>"""

POML_RESPONSE_PROMPT = """<|SYSTEM|>
You are an AI Email Response Agent using Process-Oriented Markup Language (POML) for professional, concise email communication.

<|OBJECTIVE|>
Generate direct, actionable email responses without unnecessary verbosity or repetition.

<|PROCESS|>
1. **Understand Context**:
   - Review original email content
   - Identify key points requiring response
   - Determine required actions

2. **Structure Response** (CONCISE FORMAT):
   - Brief greeting (just "Dear [Name],")
   - Get straight to the point - NO lengthy acknowledgements
   - Address the core issue with specific information
   - Provide clear next steps or action items
   - Simple closing

3. **Apply Tone**:
   - Professional and direct
   - No flowery language or excessive politeness
   - Focus on substance over form

4. **Quality Standards**:
   - Keep responses under 150 words
   - One sentence per point - no rambling
   - Direct statements, no filler words
   - Actionable information only

<|STRICT_RULES|>
❌ DO NOT:
- Quote or repeat what the sender said
- Use phrases like "Thank you for your prompt acknowledgment"
- Use phrases like "We appreciate you confirming..."
- Include unnecessary acknowledgements
- Repeat information already stated
- Use verbose transitions like "As you mentioned" or "Regarding your email about"
- Include meta-commentary about the conversation

✅ DO:
- Get directly to the point
- Provide specific, actionable information
- Be clear and concise
- Include only essential next steps
- Use simple, direct language

<|CONSTRAINTS|>
- Maximum 150 words per response
- One brief acknowledgement maximum (optional)
- Focus on what needs to happen next
- For complaints: solution only, skip empathy statements
- For inquiries: direct answer only
- For clarifications: specific information needed
- Never make commitments without approval
- Never share confidential information

<|EXAMPLE_GOOD_RESPONSE|>
Dear Dhivya,

Please review invoice INV-2024-305 and confirm the unit price of $81.08. If this differs from your records or the purchase order (PO-2024-4777), provide the correct amount.

You can:
- Upload a corrected invoice at https://portal.genbooks.com/upload
- Reply with the correct pricing details

Best regards,
GenWorx Automation Team
genworxautomation@gmail.com

<|EXAMPLE_BAD_RESPONSE|>
Dear Dhivya,

Thank you for your prompt acknowledgment. We appreciate you confirming receipt.

As you mentioned regarding the invoice discrepancy: "Thank you for the clarification."

To proceed, please review...
[TOO VERBOSE - quotes sender, unnecessary acknowledgement]

<|OUTPUT_FORMAT|>
SUBJECT: [Keep original subject, just add Re: if needed]

[Concise email body - maximum 150 words]

Best regards,
GenWorx Automation Team
genworxautomation@gmail.com
</|SYSTEM|>"""


class EmailAutoResponder:
    """Automated email analyzer and responder with POML-based prompts."""
    
    def __init__(
        self,
        settings: Settings,
        agent_email: str = "genworxautomation@gmail.com",
        dry_run: bool = False
    ):
        """
        Initialize the auto-responder.
        
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
        
        # Override analyser prompts with POML versions
        self.analyser.ANALYSIS_SYSTEM_PROMPT = POML_ANALYSIS_PROMPT
        self.analyser.RESPONSE_SYSTEM_PROMPT = POML_RESPONSE_PROMPT
        
        # Statistics
        self.stats = {
            'emails_processed': 0,
            'auto_responses_sent': 0,
            'escalated': 0,
            'validation_failures': 0,  # NEW: Track Guardrails validation failures
            'errors': 0,
            'start_time': datetime.now()
        }
        
        logger.info(f"Email Auto-Responder initialized for {agent_email}")
        if dry_run:
            console.print("[yellow]⚠️  DRY RUN MODE: Responses will not be sent[/yellow]")
    
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
        Process a single email: analyze and optionally respond.
        
        Args:
            email: EmailMessage to process
            
        Returns:
            Dictionary with processing summary
        """
        console.print(f"\n[bold]Processing:[/bold] {email.subject[:60]}...")
        console.print(f"[dim]From: {email.sender}[/dim]")
        
        # Analyze the email
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
                
                # 🛡️ GUARDRAILS AI VALIDATION
                console.print("[dim]🛡️  Validating response with Guardrails AI...[/dim]")
                is_valid, validation_error = validate_email_response(
                    response_draft.subject,
                    response_draft.body_text
                )
                
                if not is_valid:
                    # Validation failed - escalate to manual review
                    console.print(f"[red]❌ Response validation failed: {validation_error}[/red]")
                    console.print("[yellow]⚠️  Escalating to manual review due to validation failure[/yellow]")
                    logger.warning(f"Guardrails validation failed: {validation_error}")
                    
                    self.stats['validation_failures'] += 1
                    self.stats['escalated'] += 1
                    
                    result['status'] = 'validation_failed'
                    result['validation_error'] = validation_error
                    result['response_draft'] = response_draft
                    return result
                
                # Validation passed!
                console.print("[green]✅ Response passed Guardrails validation[/green]")
                
                if self.dry_run:
                    console.print("[yellow]📝 DRY RUN: Would send this validated response:[/yellow]")
                    self._display_draft(response_draft)
                    result['status'] = 'dry_run'
                else:
                    # Send the validated response
                    with self.smtp_client.connect():
                        message_id = self.smtp_client.send(response_draft)
                    
                    console.print(f"[green]✓ Validated response sent! Message ID: {message_id}[/green]")
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
        # These often get categorized as "other" but should get acknowledgment
        is_reply = email.subject.startswith('Re:') or email.subject.startswith('RE:')
        
        # ENHANCED: Check BOTH subject and body for clarification/issue keywords
        clarification_keywords = [
            'issue', 'issues',
            'clarification', 'clarify', 'clarifications',
            'question', 'questions',
            'concern', 'concerns',
            'problem', 'problems',
            'help', 'assistance',
            'confusion', 'confused',  # NEW
            'discrepancy', 'discrepancies',  # NEW
            'explain', 'explanation',  # NEW
            'understand', 'understanding',  # NEW
            'unclear', 'not clear'  # NEW
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
        
        console.print(Panel(table, title="📊 Analysis Results", border_style="cyan"))
    
    def _display_draft(self, draft: EmailDraft):
        """Display email draft in a formatted panel."""
        content = f"""[bold]Subject:[/bold] {draft.subject}
[bold]To:[/bold] {draft.to[0]}

{draft.body_text[:500]}{"..." if len(draft.body_text) > 500 else ""}
"""
        console.print(Panel(content, title="📧 Response Draft", border_style="green"))
    
    def display_statistics(self):
        """Display processing statistics."""
        uptime = datetime.now() - self.stats['start_time']
        
        stats_table = Table(title="📈 Auto-Responder Statistics", show_header=True)
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Count", style="white", justify="right")
        
        stats_table.add_row("Emails Processed", str(self.stats['emails_processed']))
        stats_table.add_row("Auto-Responses Sent", str(self.stats['auto_responses_sent']))
        stats_table.add_row("Validation Failures", str(self.stats['validation_failures']))  # NEW
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
            f"[bold cyan]🤖 Email Auto-Responder Started[/bold cyan]\n\n"
            f"[cyan]Monitoring:[/cyan] {self.agent_email}\n"
            f"[cyan]Check Interval:[/cyan] {check_interval} seconds\n"
            f"[cyan]Mode:[/cyan] {'DRY RUN' if self.dry_run else 'LIVE'}\n\n"
            "[dim]The system will automatically:\n"
            "• Monitor incoming emails\n"
            "• Analyze content using POML-based AI\n"
            "• Generate contextual responses\n"
            "• Validate responses with Guardrails AI\n"  # NEW
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
        description="Automated Email Analyzer and Responder with POML",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python email_auto_responder.py                    # Run with 30s interval
  python email_auto_responder.py --interval 60      # Check every minute
  python email_auto_responder.py --dry-run          # Test without sending
  python email_auto_responder.py --interval 10 --dry-run  # Quick testing
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
    responder = EmailAutoResponder(
        settings=settings,
        agent_email=args.agent_email,
        dry_run=args.dry_run
    )
    
    responder.run_polling(check_interval=args.interval)


if __name__ == "__main__":
    main()
