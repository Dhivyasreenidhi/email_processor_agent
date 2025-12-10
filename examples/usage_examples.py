"""
Example usage of Email Processor Agent.

This script demonstrates how to use the agent for:
1. Fetching and analyzing emails
2. Generating new emails
3. Generating responses to emails
"""

import logging
from rich.console import Console
from rich.panel import Panel

# Configure logging
logging.basicConfig(level=logging.INFO)
console = Console()


def example_fetch_and_analyze():
    """Example: Fetch and analyze unread emails."""
    from email_processor.agent import EmailProcessorAgent
    
    console.print(Panel.fit(
        "[bold cyan]Example: Fetch and Analyze Emails[/bold cyan]",
        border_style="cyan"
    ))
    
    # Initialize agent
    agent = EmailProcessorAgent()
    
    # Fetch unread emails
    emails = agent.fetch_unread_emails(limit=3)
    
    for email in emails:
        console.print(f"\n[bold]Email:[/bold] {email.subject}")
        console.print(f"[bold]From:[/bold] {email.sender}")
        
        # Analyze the email
        analysis = agent.analyze_email(email)
        
        console.print(f"[green]Category:[/green] {analysis.category.value}")
        console.print(f"[yellow]Priority:[/yellow] {analysis.priority.value}")
        console.print(f"[blue]Sentiment:[/blue] {analysis.sentiment.value}")
        console.print(f"[white]Summary:[/white] {analysis.summary}")
        
        if analysis.action_required:
            console.print("[red]⚠️ Action Required[/red]")
            
            # Generate suggested response
            response = agent.suggest_response(email, analysis)
            console.print(f"\n[bold]Suggested Response:[/bold]")
            console.print(f"Subject: {response.subject}")
            console.print(f"Body:\n{response.body_text[:300]}...")


def example_generate_email():
    """Example: Generate a new email."""
    from email_processor.agent import EmailProcessorAgent
    
    console.print(Panel.fit(
        "[bold cyan]Example: Generate New Email[/bold cyan]",
        border_style="cyan"
    ))
    
    agent = EmailProcessorAgent()
    
    # Generate a meeting request email
    draft = agent.generate_email(
        purpose="Schedule a meeting to discuss the Q4 marketing strategy and budget allocation",
        recipient_email="team@example.com",
        recipient_name="Marketing Team",
        tone="professional but friendly",
        key_points=[
            "Review Q3 results",
            "Discuss Q4 campaigns",
            "Allocate budget for new initiatives"
        ],
        signature_name="Project Manager"
    )
    
    agent.display_draft(draft)
    
    # Uncomment to send:
    # agent.send_email(draft)


def example_generate_follow_up():
    """Example: Generate a follow-up email."""
    from email_processor.agent import EmailProcessorAgent
    
    console.print(Panel.fit(
        "[bold cyan]Example: Generate Follow-up Email[/bold cyan]",
        border_style="cyan"
    ))
    
    agent = EmailProcessorAgent()
    
    # Generate a follow-up email
    draft = agent.generate_follow_up(
        original_subject="Project Proposal - New Client Portal",
        original_context="Sent a detailed proposal for building a new client portal with features like document management, messaging, and reporting",
        recipient_email="client@example.com",
        recipient_name="John Smith",
        days_since=5,
        signature_name="Your Name"
    )
    
    agent.display_draft(draft)


def example_process_inbox():
    """Example: Process entire inbox."""
    from email_processor.agent import EmailProcessorAgent
    
    console.print(Panel.fit(
        "[bold cyan]Example: Process Inbox[/bold cyan]",
        border_style="cyan"
    ))
    
    agent = EmailProcessorAgent()
    
    # Process inbox (analyze all unread + generate responses)
    results = agent.process_inbox(
        auto_respond=False,  # Don't auto-send, just generate drafts
        limit=5
    )
    
    # Review results
    for result in results:
        if result.response_draft:
            console.print(f"\n[bold]Ready to respond to:[/bold] {result.email.subject}")
            agent.display_draft(result.response_draft)


def example_with_callbacks():
    """Example: Using event callbacks."""
    from email_processor.agent import EmailProcessorAgent
    
    console.print(Panel.fit(
        "[bold cyan]Example: Event Callbacks[/bold cyan]",
        border_style="cyan"
    ))
    
    agent = EmailProcessorAgent()
    
    # Register callbacks
    @agent.on_email_received
    def on_email(email):
        console.print(f"[cyan]📥 Received:[/cyan] {email.subject}")
    
    @agent.on_email_analyzed
    def on_analysis(email, analysis):
        emoji = {
            "positive": "😊",
            "neutral": "😐",
            "negative": "😟"
        }.get(analysis.sentiment.value, "📧")
        console.print(f"[green]🔍 Analyzed:[/green] {email.subject} {emoji}")
    
    @agent.on_response_generated
    def on_response(email, draft):
        console.print(f"[yellow]✍️ Response ready:[/yellow] {draft.subject}")
    
    # Now fetch and analyze some emails
    emails = agent.fetch_unread_emails(limit=3)
    
    for email in emails:
        analysis = agent.analyze_email(email)
        if analysis.action_required:
            agent.suggest_response(email, analysis)


if __name__ == "__main__":
    console.print(Panel.fit(
        "[bold green]Email Processor Agent - Examples[/bold green]\n"
        "[dim]Make sure to configure your .env file first![/dim]",
        border_style="green"
    ))
    
    console.print("\nAvailable examples:")
    console.print("  1. Fetch and Analyze")
    console.print("  2. Generate Email")
    console.print("  3. Generate Follow-up")
    console.print("  4. Process Inbox")
    console.print("  5. Event Callbacks")
    
    console.print("\n[yellow]Uncomment the example you want to run in this file.[/yellow]")
    
    # Uncomment the example you want to run:
    # example_fetch_and_analyze()
    # example_generate_email()
    # example_generate_follow_up()
    # example_process_inbox()
    # example_with_callbacks()
