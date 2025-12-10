"""
CLI interface for Email Processor Agent.

Provides command-line tools for email generation, analysis, and processing.
"""

import logging
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table

from email_processor.config import get_settings, Settings
from email_processor.agent import EmailProcessorAgent
from email_processor.models import EmailPriority

app = typer.Typer(
    name="email-agent",
    help="AI-powered Email Processor Agent - Generate and analyze emails with AI"
)
console = Console()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def get_agent() -> EmailProcessorAgent:
    """Get configured agent instance."""
    try:
        settings = get_settings()
        return EmailProcessorAgent(settings)
    except Exception as e:
        console.print(f"[red]Failed to initialize agent: {e}[/red]")
        console.print("[yellow]Make sure you have configured your .env file[/yellow]")
        raise typer.Exit(1)


@app.command()
def fetch(
    limit: int = typer.Option(10, "--limit", "-l", help="Number of emails to fetch"),
    unread_only: bool = typer.Option(True, "--unread/--all", help="Fetch only unread emails"),
    folder: str = typer.Option("INBOX", "--folder", "-f", help="Folder to fetch from")
):
    """Fetch emails from your Gmail inbox."""
    agent = get_agent()
    
    if unread_only:
        emails = agent.fetch_unread_emails(folder=folder, limit=limit)
    else:
        emails = agent.fetch_recent_emails(folder=folder, limit=limit)
    
    if not emails:
        console.print("[yellow]No emails found[/yellow]")
        return
    
    table = Table(title=f"Emails from {folder}", show_header=True)
    table.add_column("#", style="dim")
    table.add_column("From", style="cyan", max_width=30)
    table.add_column("Subject", style="white", max_width=50)
    table.add_column("Date", style="green")
    table.add_column("📎", style="yellow", justify="center")
    
    for i, email in enumerate(emails, 1):
        table.add_row(
            str(i),
            str(email.sender)[:30],
            email.subject[:50],
            email.date.strftime("%Y-%m-%d %H:%M"),
            str(len(email.attachments)) if email.attachments else "-"
        )
    
    console.print(table)


@app.command()
def analyze(
    limit: int = typer.Option(5, "--limit", "-l", help="Number of emails to analyze"),
    folder: str = typer.Option("INBOX", "--folder", "-f", help="Folder to analyze from")
):
    """Analyze unread emails and show insights."""
    agent = get_agent()
    
    # Fetch emails
    emails = agent.fetch_unread_emails(folder=folder, limit=limit)
    
    if not emails:
        console.print("[yellow]No unread emails to analyze[/yellow]")
        return
    
    # Analyze each email
    for email in emails:
        console.print("\n" + "="*60)
        agent.display_email(email)
        
        analysis = agent.analyze_email(email)
        agent.display_analysis(analysis)
        
        if analysis.action_required:
            if Confirm.ask("\n[cyan]Generate response?[/cyan]"):
                draft = agent.suggest_response(email, analysis)
                agent.display_draft(draft)
                
                if Confirm.ask("\n[cyan]Send this response?[/cyan]"):
                    agent.send_email(draft)


@app.command()
def process(
    auto_respond: bool = typer.Option(False, "--auto-respond", "-a", help="Automatically send responses"),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum emails to process")
):
    """Process unread emails through the full pipeline."""
    agent = get_agent()
    
    results = agent.process_inbox(auto_respond=auto_respond, limit=limit)
    
    if not results:
        console.print("[yellow]No emails were processed[/yellow]")
        return
    
    # Show drafts that need review
    drafts_to_review = [r for r in results if r.response_draft and not r.response_sent]
    
    if drafts_to_review:
        console.print(f"\n[cyan]📝 {len(drafts_to_review)} responses ready for review:[/cyan]")
        
        for result in drafts_to_review:
            console.print("\n" + "-"*40)
            console.print(f"[bold]Original:[/bold] {result.email.subject}")
            agent.display_draft(result.response_draft)
            
            if Confirm.ask("Send this response?"):
                agent.send_email(result.response_draft)


@app.command()
def generate(
    purpose: str = typer.Argument(..., help="Purpose of the email to generate"),
    to: str = typer.Option(..., "--to", "-t", help="Recipient email address"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Recipient name"),
    tone: str = typer.Option("professional", "--tone", help="Tone of the email"),
    signature: Optional[str] = typer.Option(None, "--signature", "-s", help="Your name for signature"),
    send: bool = typer.Option(False, "--send", help="Send the email immediately")
):
    """Generate a new email using AI."""
    agent = get_agent()
    
    draft = agent.generate_email(
        purpose=purpose,
        recipient_email=to,
        recipient_name=name,
        tone=tone,
        signature_name=signature
    )
    
    agent.display_draft(draft)
    
    if send or Confirm.ask("\n[cyan]Send this email?[/cyan]"):
        agent.send_email(draft)
        console.print("[green]✓ Email sent successfully![/green]")
    else:
        console.print("[yellow]Email saved as draft (not sent)[/yellow]")


@app.command()
def follow_up(
    subject: str = typer.Argument(..., help="Original email subject"),
    context: str = typer.Option(..., "--context", "-c", help="What was the original email about"),
    to: str = typer.Option(..., "--to", "-t", help="Recipient email address"),
    days: int = typer.Option(7, "--days", "-d", help="Days since original email"),
    signature: Optional[str] = typer.Option(None, "--signature", "-s", help="Your name for signature"),
    send: bool = typer.Option(False, "--send", help="Send the email immediately")
):
    """Generate a follow-up email."""
    agent = get_agent()
    
    draft = agent.generate_follow_up(
        original_subject=subject,
        original_context=context,
        recipient_email=to,
        days_since=days,
        signature_name=signature
    )
    
    agent.display_draft(draft)
    
    if send or Confirm.ask("\n[cyan]Send this follow-up?[/cyan]"):
        agent.send_email(draft)
        console.print("[green]✓ Follow-up sent successfully![/green]")


@app.command()
def respond(
    email_uid: int = typer.Argument(..., help="UID of the email to respond to"),
    intent: str = typer.Option(..., "--intent", "-i", help="Intent of your response"),
    tone: str = typer.Option("professional", "--tone", help="Tone of the response"),
    send: bool = typer.Option(False, "--send", help="Send the response immediately")
):
    """Generate a response to a specific email by UID."""
    agent = get_agent()
    
    # Fetch the specific email
    with agent.imap_client.connect():
        agent.imap_client.select_folder("INBOX")
        emails = list(agent.imap_client.fetch_emails([email_uid]))
    
    if not emails:
        console.print(f"[red]Email with UID {email_uid} not found[/red]")
        raise typer.Exit(1)
    
    email = emails[0]
    console.print("\n[bold]Original Email:[/bold]")
    agent.display_email(email)
    
    # Generate response
    draft = agent.generate_response(email, intent=intent, tone=tone)
    agent.display_draft(draft)
    
    if send or Confirm.ask("\n[cyan]Send this response?[/cyan]"):
        agent.send_email(draft)
        console.print("[green]✓ Response sent successfully![/green]")


@app.command()
def poll(
    auto_respond: bool = typer.Option(False, "--auto-respond", "-a", help="Automatically send responses"),
    interval: Optional[int] = typer.Option(None, "--interval", "-i", help="Poll interval in seconds")
):
    """Run the agent in continuous polling mode."""
    agent = get_agent()
    
    if interval:
        agent.settings.poll_interval_seconds = interval
    
    console.print(Panel.fit(
        "[bold green]Starting Email Processor Agent[/bold green]\n"
        "[dim]The agent will continuously monitor your inbox[/dim]",
        border_style="green"
    ))
    
    agent.run_polling(auto_respond=auto_respond)


@app.command()
def interactive():
    """Run the agent in interactive mode with a menu."""
    agent = get_agent()
    
    console.print(Panel.fit(
        "[bold cyan]🤖 Email Processor Agent - Interactive Mode[/bold cyan]",
        border_style="cyan"
    ))
    
    while True:
        console.print("\n[bold]Menu:[/bold]")
        console.print("  [1] Fetch unread emails")
        console.print("  [2] Analyze inbox")
        console.print("  [3] Generate new email")
        console.print("  [4] Generate follow-up")
        console.print("  [5] Process inbox")
        console.print("  [6] Start polling mode")
        console.print("  [0] Exit")
        
        choice = Prompt.ask("\nSelect option", choices=["0", "1", "2", "3", "4", "5", "6"])
        
        try:
            if choice == "0":
                console.print("[yellow]Goodbye![/yellow]")
                break
            elif choice == "1":
                limit = int(Prompt.ask("Number of emails", default="10"))
                agent.fetch_unread_emails(limit=limit)
            elif choice == "2":
                limit = int(Prompt.ask("Number of emails to analyze", default="5"))
                emails = agent.fetch_unread_emails(limit=limit)
                for email in emails:
                    agent.display_email(email)
                    analysis = agent.analyze_email(email)
                    agent.display_analysis(analysis)
            elif choice == "3":
                purpose = Prompt.ask("Purpose of the email")
                to = Prompt.ask("Recipient email")
                name = Prompt.ask("Recipient name", default="")
                tone = Prompt.ask("Tone", default="professional")
                signature = Prompt.ask("Your name for signature", default="")
                
                draft = agent.generate_email(
                    purpose=purpose,
                    recipient_email=to,
                    recipient_name=name or None,
                    tone=tone,
                    signature_name=signature or None
                )
                agent.display_draft(draft)
                
                if Confirm.ask("Send this email?"):
                    agent.send_email(draft)
            elif choice == "4":
                subject = Prompt.ask("Original subject")
                context = Prompt.ask("Original email context")
                to = Prompt.ask("Recipient email")
                days = int(Prompt.ask("Days since original", default="7"))
                
                draft = agent.generate_follow_up(
                    original_subject=subject,
                    original_context=context,
                    recipient_email=to,
                    days_since=days
                )
                agent.display_draft(draft)
                
                if Confirm.ask("Send this follow-up?"):
                    agent.send_email(draft)
            elif choice == "5":
                auto = Confirm.ask("Auto-send responses?")
                agent.process_inbox(auto_respond=auto)
            elif choice == "6":
                auto = Confirm.ask("Auto-send responses?")
                agent.run_polling(auto_respond=auto)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


@app.command()
def config():
    """Show current configuration (without secrets)."""
    try:
        settings = get_settings()
        
        table = Table(title="Configuration", show_header=True)
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Gmail Email", settings.gmail_email)
        table.add_row("IMAP Server", settings.imap_connection_string)
        table.add_row("SMTP Server", settings.smtp_connection_string)
        table.add_row("Poll Interval", f"{settings.poll_interval_seconds}s")
        table.add_row("Max Emails/Batch", str(settings.max_emails_per_batch))
        table.add_row("Auto Respond", str(settings.auto_respond))
        table.add_row("Log Level", settings.log_level)
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Configuration error: {e}[/red]")
        console.print("\n[yellow]Please copy .env.example to .env and configure:[/yellow]")
        console.print("  cp .env.example .env")
        console.print("  # Edit .env with your Gmail credentials and API key")


# ============================================================================
# APPROVAL WORKFLOW COMMANDS
# ============================================================================

@app.command()
def submit_approval(
    purpose: str = typer.Argument(..., help="Purpose of the email to generate"),
    final_to: str = typer.Option(..., "--final-to", "-f", help="Final recipient email (after approval)"),
    approver: str = typer.Option(..., "--approver", "-a", help="Approver email (CFO)"),
    final_name: Optional[str] = typer.Option(None, "--final-name", help="Final recipient name"),
    tone: str = typer.Option("professional", "--tone", help="Tone of the email"),
    signature: Optional[str] = typer.Option(None, "--signature", "-s", help="Your name for signature"),
):
    """Generate an email and submit it for approval before sending."""
    from email_processor.approval_workflow import ApprovalWorkflow
    
    agent = get_agent()
    settings = get_settings()
    
    # Generate the draft
    console.print("[cyan]✍️ Generating email draft...[/cyan]")
    draft = agent.generate_email(
        purpose=purpose,
        recipient_email=final_to,  # This will be replaced after approval
        recipient_name=final_name,
        tone=tone,
        signature_name=signature
    )
    
    agent.display_draft(draft)
    
    if not Confirm.ask("\n[cyan]Submit this draft for approval?[/cyan]"):
        console.print("[yellow]Cancelled[/yellow]")
        return
    
    # Submit for approval
    workflow = ApprovalWorkflow(settings, approver_email=approver)
    request = workflow.submit_for_approval(
        draft=draft,
        final_recipient_email=final_to,
        final_recipient_name=final_name
    )
    
    console.print(Panel.fit(
        f"[bold green]✓ Submitted for Approval![/bold green]\n\n"
        f"Request ID: [bold]{request.request_id}[/bold]\n"
        f"Approver: {approver}\n"
        f"Final Recipient: {final_to}\n\n"
        f"[dim]The approver will receive an email with the draft.\n"
        f"Run 'email-agent check-approvals' to check for responses.[/dim]",
        border_style="green"
    ))


@app.command()
def check_approvals(
    approver: str = typer.Option(..., "--approver", "-a", help="Approver email to check responses from"),
):
    """Check for approval responses and process approved emails."""
    from email_processor.approval_workflow import ApprovalWorkflow
    
    settings = get_settings()
    workflow = ApprovalWorkflow(settings, approver_email=approver)
    
    # Show pending approvals first
    workflow.list_pending()
    
    # Check for responses
    processed = workflow.check_approvals()
    
    if processed:
        console.print(f"\n[green]✓ Processed {len(processed)} approval(s)[/green]")
    else:
        console.print("\n[yellow]No new approval responses found[/yellow]")


@app.command()
def list_approvals(
    approver: str = typer.Option(..., "--approver", "-a", help="Approver email"),
):
    """List all pending approval requests."""
    from email_processor.approval_workflow import ApprovalWorkflow
    
    settings = get_settings()
    workflow = ApprovalWorkflow(settings, approver_email=approver)
    
    workflow.list_pending()


@app.command()
def approval_poll(
    approver: str = typer.Option(..., "--approver", "-a", help="Approver email to monitor"),
    interval: int = typer.Option(30, "--interval", "-i", help="Check interval in seconds"),
):
    """Run continuous polling for approval responses."""
    from email_processor.approval_workflow import ApprovalWorkflow
    
    settings = get_settings()
    workflow = ApprovalWorkflow(settings, approver_email=approver)
    
    workflow.run_polling(check_interval=interval)


@app.command()
def quick_approval(
    purpose: str = typer.Argument(..., help="Purpose of the email"),
    final_to: str = typer.Option("dhivyasreenidhidurai@gmail.com", "--final-to", "-f", help="Final recipient email"),
    approver: str = typer.Option("arunsukumar03@gmail.com", "--approver", "-a", help="CFO/Approver email"),
    final_name: Optional[str] = typer.Option(None, "--final-name", help="Final recipient name"),
    tone: str = typer.Option("professional", "--tone", help="Tone of the email"),
    signature: Optional[str] = typer.Option(None, "--signature", "-s", help="Your name for signature"),
    wait_for_approval: bool = typer.Option(True, "--wait/--no-wait", help="Wait and poll for approval"),
    poll_interval: int = typer.Option(30, "--interval", "-i", help="Poll interval in seconds"),
):
    """
    Quick approval workflow with default CFO and recipient.
    
    Generates email → Sends to CFO for approval → Auto-sends to final recipient upon approval.
    """
    from email_processor.approval_workflow import ApprovalWorkflow
    
    agent = get_agent()
    settings = get_settings()
    
    # Generate the draft
    console.print(Panel.fit(
        f"[bold cyan]📧 Quick Approval Workflow[/bold cyan]\n\n"
        f"CFO (Approver): {approver}\n"
        f"Final Recipient: {final_to}",
        border_style="cyan"
    ))
    
    console.print("\n[cyan]✍️ Generating email draft...[/cyan]")
    draft = agent.generate_email(
        purpose=purpose,
        recipient_email=final_to,
        recipient_name=final_name,
        tone=tone,
        signature_name=signature
    )
    
    agent.display_draft(draft)
    
    if not Confirm.ask("\n[cyan]Submit this draft for CFO approval?[/cyan]"):
        console.print("[yellow]Cancelled[/yellow]")
        return
    
    # Submit for approval
    workflow = ApprovalWorkflow(settings, approver_email=approver)
    request = workflow.submit_for_approval(
        draft=draft,
        final_recipient_email=final_to,
        final_recipient_name=final_name
    )
    
    console.print(Panel.fit(
        f"[bold green]✓ Sent to CFO for Approval![/bold green]\n\n"
        f"Request ID: [bold]{request.request_id}[/bold]\n"
        f"Subject: {draft.subject}\n\n"
        f"[dim]CFO should reply with 'APPROVED' or 'REJECTED'[/dim]",
        border_style="green"
    ))
    
    if wait_for_approval:
        console.print(f"\n[cyan]⏳ Waiting for CFO approval (checking every {poll_interval}s)...[/cyan]")
        console.print("[dim]Press Ctrl+C to stop waiting[/dim]\n")
        workflow.run_polling(check_interval=poll_interval)


if __name__ == "__main__":
    app()

