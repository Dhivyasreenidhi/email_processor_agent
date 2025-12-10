#!/usr/bin/env python3
"""
Automated Email Workflow with CFO Approval.

Generates test emails (discrepancy and regular), sends to CFO for approval,
and upon approval, automatically sends to the vendor.

CFO Email: arunsukumar03@gmail.com
Vendor Email: dhivyasreenidhidurai@gmail.com
"""

import logging
import time
import sys
from datetime import datetime
from typing import List
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from email_processor.config import Settings, get_settings
from email_processor.models import EmailDraft, EmailAddress
from email_processor.email_generator import EmailGenerator
from email_processor.approval_workflow import ApprovalWorkflow, ApprovalRequest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
console = Console()

# Configuration
CFO_EMAIL = "arunsukumar03@gmail.com"
VENDOR_EMAIL = "dhivyasreenidhidurai@gmail.com"
VENDOR_NAME = "Dhivya Sreenidhi Durai"


# Email templates for discrepancy emails
DISCREPANCY_EMAIL_TEMPLATES = [
    {
        "purpose": "Invoice discrepancy notification - incorrect unit price",
        "context": "Invoice #INV-2024-001 shows unit price of $150 but PO #PO-2024-789 states $125. Total overcharge of $250 across 10 units.",
        "key_points": [
            "Invoice Number: INV-2024-001",
            "PO Number: PO-2024-789",
            "Discrepancy: Unit price mismatch ($150 vs $125)",
            "Amount affected: $250 overcharge",
            "Request for credit note"
        ]
    },
    {
        "purpose": "Quantity mismatch in invoice - goods received vs billed",
        "context": "Invoice #INV-2024-002 bills for 500 units but only 450 units were received as per GRN #GRN-2024-456. Requesting adjustment.",
        "key_points": [
            "Invoice Number: INV-2024-002",
            "GRN Number: GRN-2024-456",
            "Discrepancy: 50 units overbilled",
            "Value difference: $5,000",
            "Request for revised invoice"
        ]
    },
    {
        "purpose": "Duplicate invoice received - billing error",
        "context": "Invoice #INV-2024-003 appears to be a duplicate of #INV-2024-001 which was already paid on Nov 15, 2024.",
        "key_points": [
            "Duplicate Invoice: INV-2024-003",
            "Original Invoice: INV-2024-001 (paid Nov 15)",
            "Invoice Amount: $12,500",
            "Request to void duplicate",
            "Payment reference: PAY-2024-892"
        ]
    },
    {
        "purpose": "GST/Tax calculation error in invoice",
        "context": "Invoice #INV-2024-004 shows 18% GST but our agreement specifies 12% under HSN 8471. Excess tax charged: $1,200.",
        "key_points": [
            "Invoice Number: INV-2024-004",
            "HSN Code: 8471",
            "Agreed GST Rate: 12%",
            "Invoiced GST Rate: 18%",
            "Excess amount: $1,200",
            "Request for revised invoice"
        ]
    },
    {
        "purpose": "Missing discount in invoice - contract terms not applied",
        "context": "Invoice #INV-2024-005 does not reflect 10% volume discount as per contract #CTR-2023-078. Missing discount value: $3,500.",
        "key_points": [
            "Invoice Number: INV-2024-005",
            "Contract Reference: CTR-2023-078",
            "Missing Discount: 10% volume discount",
            "Amount to be credited: $3,500",
            "Total invoice value: $35,000"
        ]
    }
]

# Email templates for regular (non-discrepancy) emails
REGULAR_EMAIL_TEMPLATES = [
    {
        "purpose": "Monthly statement reconciliation request",
        "context": "Requesting the monthly statement for December 2024 for our accounts reconciliation process.",
        "key_points": [
            "Statement period: December 2024",
            "Account Number: CUST-2024-789",
            "Format: PDF and Excel preferred",
            "Urgency: Required by Dec 15"
        ]
    },
    {
        "purpose": "Purchase order confirmation",
        "context": "Confirming receipt and acceptance of Purchase Order #PO-2024-1234 for office supplies.",
        "key_points": [
            "PO Number: PO-2024-1234",
            "Order Value: $8,500",
            "Expected delivery: Dec 20, 2024",
            "Delivery address confirmed"
        ]
    },
    {
        "purpose": "Payment schedule update notification",
        "context": "Informing about updated payment schedule for Q1 2025 as per our revised terms agreement.",
        "key_points": [
            "New payment terms: Net 45",
            "Effective from: Jan 1, 2025",
            "Monthly payment date: 15th",
            "Wire transfer details enclosed"
        ]
    },
    {
        "purpose": "Vendor performance review meeting invitation",
        "context": "Scheduling quarterly vendor review meeting to discuss performance metrics and future requirements.",
        "key_points": [
            "Meeting Date: Dec 18, 2024",
            "Time: 2:00 PM - 3:30 PM",
            "Location: Virtual (Teams)",
            "Agenda: Q4 performance, Q1 planning"
        ]
    },
    {
        "purpose": "Thank you for timely delivery",
        "context": "Expressing appreciation for the excellent service and timely delivery of our recent order.",
        "key_points": [
            "Order Reference: ORD-2024-567",
            "Delivery date: Dec 5, 2024",
            "Quality: Excellent",
            "Appreciation for partnership"
        ]
    }
]


def generate_test_emails(settings: Settings) -> List[EmailDraft]:
    """Generate 10 test emails using AI - 5 discrepancy and 5 regular."""
    
    console.print(Panel.fit(
        "[bold cyan]🤖 Generating Test Emails with AI[/bold cyan]\n"
        "Generating 5 discrepancy emails and 5 regular emails",
        border_style="cyan"
    ))
    
    email_generator = EmailGenerator(settings)
    drafts = []
    
    # Generate discrepancy emails
    console.print("\n[bold yellow]📋 Generating 5 DISCREPANCY emails...[/bold yellow]")
    for i, template in enumerate(DISCREPANCY_EMAIL_TEMPLATES, 1):
        with console.status(f"[cyan]Generating discrepancy email {i}/5...[/cyan]"):
            draft = email_generator.generate_simple(
                purpose=template["purpose"],
                recipient_email=VENDOR_EMAIL,
                recipient_name=VENDOR_NAME,
                tone="professional but firm",
                signature_name="Accounts Payable Team"
            )
            # Add context to the draft
            draft.body_text = f"""Dear {VENDOR_NAME},

{draft.body_text}

Key Details:
""" + "\n".join([f"• {point}" for point in template["key_points"]]) + """

Please review this discrepancy and provide a resolution at your earliest convenience.

Best regards,
Accounts Payable Team"""
            
            drafts.append({
                "draft": draft,
                "type": "DISCREPANCY",
                "template": template
            })
            console.print(f"  [green]✓[/green] Discrepancy Email {i}: {draft.subject[:50]}...")
    
    # Generate regular emails
    console.print("\n[bold green]📋 Generating 5 REGULAR emails...[/bold green]")
    for i, template in enumerate(REGULAR_EMAIL_TEMPLATES, 1):
        with console.status(f"[cyan]Generating regular email {i}/5...[/cyan]"):
            draft = email_generator.generate_simple(
                purpose=template["purpose"],
                recipient_email=VENDOR_EMAIL,
                recipient_name=VENDOR_NAME,
                tone="professional and friendly",
                signature_name="Accounts Team"
            )
            drafts.append({
                "draft": draft,
                "type": "REGULAR",
                "template": template
            })
            console.print(f"  [green]✓[/green] Regular Email {i}: {draft.subject[:50]}...")
    
    return drafts


def display_email_summary(drafts: List[dict]):
    """Display a summary table of generated emails."""
    table = Table(title="📧 Generated Emails Summary", show_header=True, header_style="bold magenta")
    table.add_column("#", style="cyan", width=3)
    table.add_column("Type", style="yellow", width=12)
    table.add_column("Subject", style="white", max_width=50)
    table.add_column("Recipient", style="green", width=30)
    
    for i, item in enumerate(drafts, 1):
        draft = item["draft"]
        email_type = item["type"]
        type_style = "bold red" if email_type == "DISCREPANCY" else "bold green"
        table.add_row(
            str(i),
            f"[{type_style}]{email_type}[/{type_style}]",
            draft.subject[:48] + "..." if len(draft.subject) > 50 else draft.subject,
            VENDOR_EMAIL
        )
    
    console.print("\n")
    console.print(table)
    console.print("\n")


def submit_emails_for_approval(settings: Settings, drafts: List[dict]) -> List[ApprovalRequest]:
    """Submit all generated emails for CFO approval."""
    
    console.print(Panel.fit(
        f"[bold cyan]📨 Submitting Emails for CFO Approval[/bold cyan]\n"
        f"CFO Email: {CFO_EMAIL}\n"
        f"Vendor Email: {VENDOR_EMAIL}",
        border_style="cyan"
    ))
    
    workflow = ApprovalWorkflow(
        settings=settings,
        approver_email=CFO_EMAIL
    )
    
    approval_requests = []
    
    for i, item in enumerate(drafts, 1):
        draft = item["draft"]
        email_type = item["type"]
        
        console.print(f"\n[cyan]Submitting email {i}/10: [{email_type}] {draft.subject[:40]}...[/cyan]")
        
        try:
            request = workflow.submit_for_approval(
                draft=draft,
                final_recipient_email=VENDOR_EMAIL,
                final_recipient_name=VENDOR_NAME
            )
            approval_requests.append({
                "request": request,
                "type": email_type,
                "draft": draft
            })
            console.print(f"  [green]✓ Request ID: {request.request_id}[/green]")
            
            # Small delay between emails to avoid rate limiting
            time.sleep(1)
            
        except Exception as e:
            console.print(f"  [red]✗ Failed: {e}[/red]")
            logger.error(f"Failed to submit email for approval: {e}")
    
    return approval_requests


def display_pending_approvals(workflow: ApprovalWorkflow):
    """Display current pending approvals."""
    console.print("\n")
    workflow.list_pending()


def monitor_approvals(settings: Settings, check_interval: int = 1):
    """Monitor for CFO approvals and process them."""
    
    console.print(Panel.fit(
        f"[bold cyan]🔄 Monitoring for CFO Approvals[/bold cyan]\n"
        f"Checking every {check_interval} seconds\n"
        f"CFO: {CFO_EMAIL}\n"
        f"[dim]Press Ctrl+C to stop monitoring[/dim]",
        border_style="cyan"
    ))
    
    workflow = ApprovalWorkflow(
        settings=settings,
        approver_email=CFO_EMAIL
    )
    
    # Register callbacks
    @workflow.on_approved
    def on_email_approved(request: ApprovalRequest):
        console.print(Panel.fit(
            f"[bold green]✅ EMAIL APPROVED & SENT![/bold green]\n"
            f"Subject: {request.draft.subject}\n"
            f"Sent to: {request.final_recipient.email}\n"
            f"Approved at: {request.approved_at.strftime('%Y-%m-%d %H:%M:%S')}",
            border_style="green"
        ))
    
    @workflow.on_rejected
    def on_email_rejected(request: ApprovalRequest):
        console.print(Panel.fit(
            f"[bold red]❌ EMAIL REJECTED[/bold red]\n"
            f"Subject: {request.draft.subject}\n"
            f"Reason: {request.notes or 'No reason provided'}",
            border_style="red"
        ))
    
    # Start polling
    workflow.run_polling(check_interval=check_interval)


def run_full_workflow():
    """Run the complete email generation and approval workflow."""
    
    console.print(Panel.fit(
        "[bold magenta]🚀 EMAIL APPROVAL WORKFLOW[/bold magenta]\n\n"
        f"[cyan]CFO (Approver):[/cyan] {CFO_EMAIL}\n"
        f"[cyan]Vendor (Final Recipient):[/cyan] {VENDOR_EMAIL}\n\n"
        "[dim]This workflow will:[/dim]\n"
        "1. Generate 10 test emails (5 discrepancy + 5 regular)\n"
        "2. Send all emails to CFO for approval\n"
        "3. Monitor for CFO's response\n"
        "4. Auto-send approved emails to vendor",
        border_style="magenta"
    ))
    
    try:
        # Load settings
        settings = get_settings()
        console.print("[green]✓ Settings loaded successfully[/green]")
        
        # Step 1: Generate test emails
        console.print("\n" + "="*60)
        drafts = generate_test_emails(settings)
        
        # Display summary
        display_email_summary(drafts)
        
        # Step 2: Submit for approval
        console.print("\n" + "="*60)
        approval_requests = submit_emails_for_approval(settings, drafts)
        
        console.print(Panel.fit(
            f"[bold green]✅ All {len(approval_requests)} emails submitted for approval![/bold green]\n\n"
            f"CFO ({CFO_EMAIL}) will receive approval requests.\n"
            f"Reply with 'APPROVED' or 'REJECTED' to process each email.\n\n"
            "[dim]Starting approval monitoring...[/dim]",
            border_style="green"
        ))
        
        # Step 3: Monitor for approvals
        console.print("\n" + "="*60)
        time.sleep(2)  # Brief pause before monitoring
        monitor_approvals(settings, check_interval=1)
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Workflow stopped by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        logger.exception("Workflow failed")
        sys.exit(1)


def generate_only():
    """Only generate emails and submit for approval, then exit."""
    
    console.print(Panel.fit(
        "[bold cyan]📧 GENERATE & SUBMIT MODE[/bold cyan]\n"
        "Will generate and submit emails, then exit.\n"
        "Run with '--monitor' to watch for approvals.",
        border_style="cyan"
    ))
    
    try:
        settings = get_settings()
        
        # Generate emails
        drafts = generate_test_emails(settings)
        display_email_summary(drafts)
        
        # Submit for approval
        approval_requests = submit_emails_for_approval(settings, drafts)
        
        console.print(Panel.fit(
            f"[bold green]✅ {len(approval_requests)} emails submitted for CFO approval![/bold green]\n\n"
            f"CFO: {CFO_EMAIL}\n"
            f"Vendor: {VENDOR_EMAIL}\n\n"
            "To monitor for approvals, run:\n"
            "[cyan]python run_email_workflow.py --monitor[/cyan]",
            border_style="green"
        ))
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.exception("Failed")
        sys.exit(1)


def monitor_only():
    """Only monitor for approval responses."""
    
    console.print(Panel.fit(
        "[bold cyan]🔍 MONITORING MODE[/bold cyan]\n"
        f"Watching for approval responses from CFO ({CFO_EMAIL})",
        border_style="cyan"
    ))
    
    try:
        settings = get_settings()
        monitor_approvals(settings, check_interval=1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.exception("Failed")
        sys.exit(1)


def list_pending():
    """List all pending approvals."""
    try:
        settings = get_settings()
        workflow = ApprovalWorkflow(
            settings=settings,
            approver_email=CFO_EMAIL
        )
        workflow.list_pending()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Email Approval Workflow with CFO Approval",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_email_workflow.py              # Full workflow (generate + submit + monitor)
  python run_email_workflow.py --generate   # Only generate and submit emails
  python run_email_workflow.py --monitor    # Only monitor for approvals
  python run_email_workflow.py --list       # List pending approvals
"""
    )
    
    parser.add_argument('--generate', action='store_true', 
                       help='Only generate and submit emails, then exit')
    parser.add_argument('--monitor', action='store_true',
                       help='Only monitor for approval responses')
    parser.add_argument('--list', action='store_true',
                       help='List pending approvals')
    parser.add_argument('--interval', type=int, default=1,
                       help='Check interval in seconds (default: 1)')
    
    args = parser.parse_args()
    
    if args.list:
        list_pending()
    elif args.generate:
        generate_only()
    elif args.monitor:
        try:
            settings = get_settings()
            monitor_approvals(settings, check_interval=args.interval)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)
    else:
        run_full_workflow()
