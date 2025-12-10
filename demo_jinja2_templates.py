#!/usr/bin/env python3
"""
Demo: Using Jinja2 Email Templates

This script demonstrates how to use the professional Jinja2 email templates
for generating beautifully formatted HTML emails.
"""

from email_processor.email_templates import EmailTemplateRenderer
from email_processor.models import EmailDraft, EmailAddress
from datetime import datetime

def demo_discrepancy_email():
    """Demonstrate generating a discrepancy email using Jinja2 template."""
    
    renderer = EmailTemplateRenderer()
    
    # Sample discrepancy data
    discrepancies = [
        {
            "title": "Unit Price Mismatch",
            "type": "Price Discrepancy",
            "details": "Invoice shows $150 per unit but PO #PO-2024-789 states $125 per unit. Total overcharge: $250"
        },
        {
            "title": "Quantity Difference",
            "type": "Quantity Discrepancy", 
            "details": "Invoiced for 10 units but only 8 units were delivered as per GRN #GRN-2024-456"
        }
    ]
    
    key_points = [
        "Invoice Number: INV-2024-001",
        "PO Number: PO-2024-789",
        "Total Discrepancy Value: $250 + missing 2 units",
        "Request for revised invoice or credit note"
    ]
    
    html_body, plain_text = renderer.render_discrepancy_email(
        vendor_name="Acme Corp",
        intro_message="We have reviewed your recent invoice submission and identified some discrepancies that require your attention before we can process the payment.",
        discrepancies=discrepancies,
        key_points=key_points,
        subject="Invoice Discrepancy - Action Required",
        signature_name="Accounts Payable Team",
        company_name="GenBooks Inc.",
        reply_to_email="ap@genbooks.com",
        warning_message="Payment processing has been temporarily held pending resolution of these discrepancies.",
        include_cta=True
    )
    
    return html_body, plain_text


def demo_regular_email():
    """Demonstrate generating a regular business email using Jinja2 template."""
    
    renderer = EmailTemplateRenderer()
    
    key_points = [
        "Statement period: December 2024",
        "Account Number: CUST-2024-789",
        "Format: PDF and Excel preferred",
        "Required by: December 15, 2024"
    ]
    
    html_body, plain_text = renderer.render_regular_email(
        vendor_name="Acme Corp",
        intro_message="We are conducting our monthly account reconciliation and would like to request your assistance.",
        key_points=key_points,
        subject="Monthly Statement Request - December 2024",
        header_title="📊 Monthly Statement Request",
        details_title="Required Information",
        highlight_message="This request is part of our standard monthly closing process. Your prompt response will help us complete our reconciliation on schedule.",
        highlight_title="Please Note",
        closing_message="We appreciate your partnership and thank you in advance for your cooperation.",
        followup_message="If you have any questions or need clarification on this request, please don't hesitate to reach out.",
        signature_name="Accounts Team",
        company_name="GenBooks Inc.",
        reply_to_email="accounts@genbooks.com",
        include_cta=True,
        cta_text="Reply with Statement"
    )
    
    return html_body, plain_text


def create_email_draft_with_template(html_body: str, plain_text: str, subject: str, recipient_email: str, recipient_name: str = None) -> EmailDraft:
    """Create an EmailDraft object with Jinja2-rendered content."""
    
    return EmailDraft(
        to=[EmailAddress(email=recipient_email, name=recipient_name)],
        subject=subject,
        body_html=html_body,
        body_text=plain_text,
        created_at=datetime.now()
    )


if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    print("=" * 70)
    print("  JINJA2 EMAIL TEMPLATE DEMO")
    print("=" * 70)
    
    # Demo 1: Discrepancy Email
    print("\n📧 Generating DISCREPANCY email...")
    html_disc, text_disc = demo_discrepancy_email()
    
    # Save to file
    output_dir = Path("email_outputs")
    output_dir.mkdir(exist_ok=True)
    
    disc_html_file = output_dir / "discrepancy_email.html"
    disc_text_file = output_dir / "discrepancy_email.txt"
    
    with open(disc_html_file, 'w', encoding='utf-8') as f:
        f.write(html_disc)
    
    with open(disc_text_file, 'w', encoding='utf-8') as f:
        f.write(text_disc)
    
    print(f"✅ Discrepancy email generated:")
    print(f"   HTML: {disc_html_file}")
    print(f"   Text: {disc_text_file}")
    
    # Demo 2: Regular Email
    print("\n📧 Generating REGULAR email...")
    html_reg, text_reg = demo_regular_email()
    
    reg_html_file = output_dir / "regular_email.html"
    reg_text_file = output_dir / "regular_email.txt"
    
    with open(reg_html_file, 'w', encoding='utf-8') as f:
        f.write(html_reg)
    
    with open(reg_text_file, 'w', encoding='utf-8') as f:
        f.write(text_reg)
    
    print(f"✅ Regular email generated:")
    print(f"   HTML: {reg_html_file}")
    print(f"   Text: {reg_text_file}")
    
    # Demo 3: Create EmailDraft objects
    print("\n📦 Creating EmailDraft objects...")
    
    draft_disc = create_email_draft_with_template(
        html_body=html_disc,
        plain_text=text_disc,
        subject="Invoice Discrepancy - Action Required",
        recipient_email="vendor@example.com",
        recipient_name="Acme Corp"
    )
    
    draft_reg = create_email_draft_with_template(
        html_body=html_reg,
        plain_text=text_reg,
        subject="Monthly Statement Request - December 2024",
        recipient_email="vendor@example.com",
        recipient_name="Acme Corp"
    )
    
    print(f"✅ Discrepancy draft: {draft_disc.subject}")
    print(f"✅ Regular draft: {draft_reg.subject}")
    
    print("\n" + "=" * 70)
    print("  DEMO COMPLETE!")
    print("=" * 70)
    print(f"\n📁 Open the files in '{output_dir}' to see the beautiful emails!")
    print("\n💡 TIP: Open the HTML files in a web browser to see the full styling.")
    print("=" * 70)
