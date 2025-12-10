"""
Simple Email Template Renderer.

Renders professional HTML emails using simple string templates.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class EmailTemplateRenderer:
    """
    Email template renderer using simple string replacement.
    
    Renders HTML emails from templates with dynamic content.
    """
    
    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Initialize the template renderer.
        
        Args:
            templates_dir: Directory containing email templates
        """
        if templates_dir is None:
            # Default to project root /templates directory
            templates_dir = Path(__file__).parent.parent.parent / "templates"
        
        self.templates_dir = templates_dir
        
        logger.info(f"Email template renderer initialized. Templates dir: {templates_dir}")
    
    def render_discrepancy_email(
        self,
        vendor_name: str,
        intro_message: str,
        discrepancies: list[Dict[str, str]],
        key_points: Optional[list[str]] = None,
        subject: str = "Invoice Discrepancy Notification",
        signature_name: str = "Accounts Payable Team",
        company_name: str = "GenBooks",
        reply_to_email: str = "ap@genbooks.com",
        warning_message: Optional[str] = None,
        include_cta: bool = True,
        company_address: str = "",
        company_contact: str = "",
        **kwargs
    ) -> tuple[str, str]:
        """
        Render a discrepancy email.
        
        Returns:
            Tuple of (html_body, plain_text_body)
        """
        template_path = self.templates_dir / 'discrepancy_email.html'
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()
        
        # Build discrepancies HTML
        discrepancies_html = ""
        if discrepancies:
            disc_items = ""
            for disc in discrepancies:
                title = disc.get('title') or disc.get('type', '')
                details = disc.get('details', '')
                disc_items += f"""
            <div class="disc-item">
                <strong>{title}</strong>
                {details}
            </div>"""
            
            discrepancies_html = f"""
        <div class="section-title">
            📋 Found Discrepancies
        </div>

        <div class="discrepancy-list">{disc_items}
        </div>"""
        
        # Build key points HTML
        key_points_html = ""
        if key_points:
            points_list = "\n                ".join([f"<li>{point}</li>" for point in key_points])
            key_points_html = f"""
        <div class="section-title">
            🔑 Key Details
        </div>

        <div class="key-points">
            <ul>
                {points_list}
            </ul>
        </div>"""
        
        # Build CTA HTML
        cta_html = ""
        if include_cta:
            cta_html = f"""
        <div class="cta">
            <a href="mailto:{reply_to_email}" class="cta-button">Reply to This Email</a>
        </div>"""
        
        # Build warning HTML
        warning_html = ""
        if warning_message:
            warning_html = f"""
        <div class="warning">
            <div class="warning-icon">⚠️</div>
            <div>{warning_message}</div>
        </div>"""
        
        # Replace placeholders
        html_body = template.replace('{{SUBJECT}}', subject)
        html_body = html_body.replace('{{VENDOR_NAME}}', vendor_name)
        html_body = html_body.replace('{{INTRO_MESSAGE}}', intro_message)
        html_body = html_body.replace('{{DISCREPANCIES}}', discrepancies_html)
        html_body = html_body.replace('{{KEY_POINTS}}', key_points_html)
        html_body = html_body.replace('{{CTA}}', cta_html)
        html_body = html_body.replace('{{WARNING}}', warning_html)
        html_body = html_body.replace('{{SIGNATURE_NAME}}', signature_name)
        html_body = html_body.replace('{{COMPANY_NAME}}', company_name)
        html_body = html_body.replace('{{COMPANY_ADDRESS}}', company_address)
        html_body = html_body.replace('{{COMPANY_CONTACT}}', company_contact)
        
        # Generate plain text version
        context = {
            'vendor_name': vendor_name,
            'intro_message': intro_message,
            'discrepancies': discrepancies,
            'key_points': key_points,
            'signature_name': signature_name,
            'company_name': company_name,
        }
        plain_text = self._html_to_plain(html_body, context)
        
        return html_body, plain_text
    
    def render_regular_email(
        self,
        vendor_name: str,
        intro_message: str,
        key_points: Optional[list[str]] = None,
        subject: str = "Business Communication",
        header_title: Optional[str] = None,
        details_title: Optional[str] = None,
        highlight_message: Optional[str] = None,
        highlight_title: Optional[str] = None,
        additional_info: Optional[str] = None,
        additional_info_title: Optional[str] = None,
        closing_message: Optional[str] = None,
        followup_message: Optional[str] = None,
        signature_name: str = "Accounts Team",
        company_name: str = "GenBooks",
        reply_to_email: str = "accounts@genbooks.com",
        include_cta: bool = False,
        cta_text: Optional[str] = None,
        company_address: str = "",
        company_contact: str = "",
        footer_note: str = "Thank you for your business",
        **kwargs
    ) -> tuple[str,str]:
        """
        Render a regular business email.
        
        Returns:
            Tuple of (html_body, plain_text_body)
        """
        template_path = self.templates_dir / 'regular_email.html'
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()
        
        # Build key points HTML
        key_points_html = ""
        if key_points:
            points_list = "\n                ".join([f"<li>{point}</li>" for point in key_points])
            key_points_html = f"""
        <div class="section-title">
            🔑 {details_title or 'Important Details'}
        </div>

        <div class="key-points">
            <ul>
                {points_list}
            </ul>
        </div>"""
        
        # Build highlight HTML
        highlight_html = ""
        if highlight_message:
            highlight_html = f"""
        <div class="highlight-box">
            <strong>{highlight_title or 'Please Note:'}</strong><br>
            {highlight_message}
        </div>"""
        
        # Build additional info HTML
        additional_info_html = ""
        if additional_info:
            additional_info_html = f"""
        <div class="info-box">
            <div class="info-box-title">{additional_info_title or 'Additional Information'}</div>
            <div>{additional_info}</div>
        </div>"""
        
        # Build CTA HTML
        cta_html = ""
        if include_cta and cta_text:
            cta_html = f"""
        <div class="cta">
            <a href="mailto:{reply_to_email}" class="cta-button">{cta_text}</a>
        </div>"""
        
        # Build followup message HTML
        followup_html = ""
        if followup_message:
            followup_html = f"""
            <p>{followup_message}</p>"""
        
        # Replace placeholders
        html_body = template.replace('{{SUBJECT}}', subject)
        html_body = html_body.replace('{{HEADER_TITLE}}', header_title or '📧 Business Communication')
        html_body = html_body.replace('{{VENDOR_NAME}}', vendor_name)
        html_body = html_body.replace('{{INTRO_MESSAGE}}', intro_message)
        html_body = html_body.replace('{{KEY_POINTS}}', key_points_html)
        html_body = html_body.replace('{{HIGHLIGHT}}', highlight_html)
        html_body = html_body.replace('{{ADDITIONAL_INFO}}', additional_info_html)
        html_body = html_body.replace('{{CTA}}', cta_html)
        html_body = html_body.replace('{{CLOSING_MESSAGE}}', closing_message or 'We appreciate your partnership and look forward to continuing our collaboration.')
        html_body = html_body.replace('{{FOLLOWUP_MESSAGE}}', followup_html)
        html_body = html_body.replace('{{SIGNATURE_NAME}}', signature_name)
        html_body = html_body.replace('{{COMPANY_NAME}}', company_name)
        html_body = html_body.replace('{{COMPANY_ADDRESS}}', company_address)
        html_body = html_body.replace('{{COMPANY_CONTACT}}', company_contact)
        html_body = html_body.replace('{{FOOTER_NOTE}}', footer_note)
        
        # Generate plain text version
        context = {
            'vendor_name': vendor_name,
            'intro_message': intro_message,
            'key_points': key_points,
            'highlight_message': highlight_message,
            'highlight_title': highlight_title,
            'closing_message': closing_message,
            'signature_name': signature_name,
            'company_name': company_name,
        }
        plain_text = self._html_to_plain(html_body, context)
        
        return html_body, plain_text
    
    def _html_to_plain(self, html: str, context: Dict[str, Any]) -> str:
        """
        Convert HTML email to plain text version.
        
        For now, creates a simple plain text version from context.
        In production, you might want to use html2text library.
        """
        parts = []
        
        # Greeting
        if 'vendor_name' in context:
            parts.append(f"Dear {context['vendor_name']} Team,\n")
        
        # Intro
        if 'intro_message' in context:
            parts.append(f"{context['intro_message']}\n")
        
        # Discrepancies
        if context.get('discrepancies'):
            parts.append("\nFOUND DISCREPANCIES:\n")
            parts.append("-" * 50)
            for disc in context['discrepancies']:
                title = disc.get('title') or disc.get('type', 'Issue')
                details = disc.get('details', '')
                parts.append(f"\n• {title}\n  {details}")
            parts.append("\n")
        
        # Key points
        if context.get('key_points'):
            parts.append("\nKEY DETAILS:\n")
            for point in context['key_points']:
                parts.append(f"• {point}")
            parts.append("\n")
        
        # Highlight message
        if context.get('highlight_message'):
            parts.append(f"\n{context.get('highlight_title', 'PLEASE NOTE')}:")
            parts.append(f"{context['highlight_message']}\n")
        
        # Closing
        if context.get('closing_message'):
            parts.append(f"\n{context['closing_message']}\n")
        
        # Signature
        parts.append("\nBest regards,")
        parts.append(context.get('signature_name', 'Accounts Team'))
        parts.append(context.get('company_name', 'GenBooks'))
        
        return "\n".join(parts)
