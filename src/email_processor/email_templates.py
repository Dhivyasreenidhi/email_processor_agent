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
    
    def render_visual_discrepancy_email(
        self,
        invoice_amount: str = "12,450.00",
        po_amount: str = "10,000.00",
        variance_amount: str = "2,450.00",
        invoice_percentage: str = "124.5",
        variance_percentage: str = "24.5",
        scale_factor: str = "100",
        po_number: str = "PO-2023-04567",
        po_qty: str = "100",
        unit_price: str = "100.00",
        invoice_number: str = "INV-78901",
        invoice_qty: str = "110",
        invoice_unit_price: str = "113.18",
        qty_variance_percentage: str = "10",
        price_variance_percentage: str = "13.18",
        qty_variance: str = "10",
        price_variance: str = "13.18",
        tax_rate: str = "8.5",
        invoice_tax: str = "10.0",
        tax_variance: str = "1.5",
        discrepancy_count: str = "3",
        resolution_deadline: str = "2023-12-20",
        company_name: str = "CORPORATE INC.",
        reply_to_email: str = "ap@company.com",
        company_contact: str = "+1 (555) 123-4567",
        portal_url: str = "#",
        reference_number: str = "DISC-2023-0456-VISUAL",
        generation_date: str = "",
        **kwargs
    ) -> tuple[str, str]:
        """
        Render a visual invoice discrepancy email with bar charts and comparison boxes.
        
        Returns:
            Tuple of (html_body, plain_text_body)
        """
        from datetime import datetime
        
        if not generation_date:
            generation_date = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        html_body = f'''<div style="font-family: 'Inter', 'Segoe UI', 'SF Pro Display', -apple-system, sans-serif; line-height: 1.6; color: #111827; max-width: 780px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);">
   
    <!-- Header with Visual Alert -->
    <div style="background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%); color: #ffffff; padding: 30px 40px; text-align: left; position: relative;">
        <div style="position: absolute; right: 30px; top: 30px; background: rgba(255, 255, 255, 0.2); padding: 10px 20px; border-radius: 30px; font-size: 12px; font-weight: 700; letter-spacing: 1px;">
            ⚠️ MATCH FAILED
        </div>
        <h1 style="margin: 0 0 8px 0; font-size: 28px; font-weight: 800; letter-spacing: -0.5px; color: #ffffff;">INVOICE DISCREPANCY ALERT</h1>
        <p style="margin: 0; font-size: 15px; color: #fecaca; font-weight: 400;">Visual Discrepancy Analysis Report</p>
    </div>

    <!-- Main Content -->
    <div style="padding: 40px; background: #f9fafb;">
       
        <!-- Quick Summary Cards -->
        <div style="display: flex; gap: 15px; margin-bottom: 35px;">
            <div style="flex: 1; background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05); border-top: 5px solid #dc2626;">
                <div style="font-size: 13px; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;">Invoice Amount</div>
                <div style="font-size: 28px; font-weight: 800; color: #dc2626;">${invoice_amount}</div>
            </div>
            <div style="flex: 1; background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05); border-top: 5px solid #10b981;">
                <div style="font-size: 13px; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;">PO Amount</div>
                <div style="font-size: 28px; font-weight: 800; color: #10b981;">${po_amount}</div>
            </div>
            <div style="flex: 1; background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05); border-top: 5px solid #f59e0b;">
                <div style="font-size: 13px; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;">Variance</div>
                <div style="font-size: 28px; font-weight: 800; color: #f59e0b;">${variance_amount}</div>
            </div>
        </div>

        <!-- VISUAL DISCREPANCY GROUNDING SECTION -->
        <div style="margin: 40px 0 30px 0;">
            <div style="background: white; border-radius: 12px; padding: 30px; box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);">
                <h2 style="margin: 0 0 25px 0; font-size: 22px; font-weight: 800; color: #111827; display: flex; align-items: center;">
                    <span style="background: #dc2626; color: white; width: 36px; height: 36px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; margin-right: 12px; font-size: 18px;">!</span>
                    Visual Discrepancy Analysis
                </h2>
               
                <!-- VISUAL BAR CHART - Actual vs Expected -->
                <div style="margin-bottom: 35px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 15px;">
                        <div style="font-size: 14px; font-weight: 600; color: #374151;">Amount Comparison Visualization</div>
                        <div style="font-size: 13px; color: #6b7280;">Scale: 1px = ${scale_factor}</div>
                    </div>
                   
                    <!-- Bar Chart Container -->
                    <div style="background: #f3f4f6; border-radius: 8px; padding: 25px; position: relative;">
                       
                        <!-- Expected Amount Bar -->
                        <div style="margin-bottom: 35px;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                                <span style="font-size: 14px; font-weight: 600; color: #059669;">Expected (PO)</span>
                                <span style="font-size: 14px; font-weight: 700; color: #059669;">${po_amount}</span>
                            </div>
                            <div style="background: #d1fae5; height: 30px; border-radius: 6px; position: relative; overflow: hidden;">
                                <div style="background: linear-gradient(90deg, #10b981 0%, #34d399 100%); width: 100%; height: 100%;">
                                    <div style="position: absolute; right: 10px; top: 5px; color: #065f46; font-weight: 700; font-size: 13px;">100%</div>
                                </div>
                            </div>
                        </div>
                       
                        <!-- Invoice Amount Bar -->
                        <div style="margin-bottom: 20px;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                                <span style="font-size: 14px; font-weight: 600; color: #dc2626;">Invoice Submitted</span>
                                <span style="font-size: 14px; font-weight: 700; color: #dc2626;">${invoice_amount}</span>
                            </div>
                            <div style="background: #fee2e2; height: 30px; border-radius: 6px; position: relative; overflow: hidden;">
                                <div style="background: linear-gradient(90deg, #ef4444 0%, #f87171 100%); width: {invoice_percentage}%; height: 100%; position: relative;">
                                    <div style="position: absolute; right: 10px; top: 5px; color: #991b1b; font-weight: 700; font-size: 13px;">{invoice_percentage}%</div>
                                </div>
                            </div>
                        </div>
                       
                        <!-- Scale Ruler -->
                        <div style="border-top: 2px solid #9ca3af; margin-top: 30px; padding-top: 15px; position: relative;">
                            <div style="display: flex; justify-content: space-between; position: relative;">
                                <div style="position: absolute; left: 0%; transform: translateX(-50%);">
                                    <div style="height: 10px; width: 2px; background: #9ca3af; margin-bottom: 5px;"></div>
                                    <div style="font-size: 11px; color: #6b7280; white-space: nowrap;">$0</div>
                                </div>
                                <div style="position: absolute; left: 20%; transform: translateX(-50%);">
                                    <div style="height: 10px; width: 2px; background: #9ca3af; margin-bottom: 5px;"></div>
                                    <div style="font-size: 11px; color: #6b7280; white-space: nowrap;">$2000</div>
                                </div>
                                <div style="position: absolute; left: 40%; transform: translateX(-50%);">
                                    <div style="height: 10px; width: 2px; background: #9ca3af; margin-bottom: 5px;"></div>
                                    <div style="font-size: 11px; color: #6b7280; white-space: nowrap;">$4000</div>
                                </div>
                                <div style="position: absolute; left: 60%; transform: translateX(-50%);">
                                    <div style="height: 10px; width: 2px; background: #9ca3af; margin-bottom: 5px;"></div>
                                    <div style="font-size: 11px; color: #6b7280; white-space: nowrap;">$6000</div>
                                </div>
                                <div style="position: absolute; left: 80%; transform: translateX(-50%);">
                                    <div style="height: 10px; width: 2px; background: #9ca3af; margin-bottom: 5px;"></div>
                                    <div style="font-size: 11px; color: #6b7280; white-space: nowrap;">$8000</div>
                                </div>
                                <div style="position: absolute; left: 100%; transform: translateX(-50%);">
                                    <div style="height: 10px; width: 2px; background: #9ca3af; margin-bottom: 5px;"></div>
                                    <div style="font-size: 11px; color: #6b7280; white-space: nowrap;">$10000</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
               
                <!-- MISMATCH HIGHLIGHT BOXES -->
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin-bottom: 30px;">
                    <!-- Expected Box -->
                    <div style="background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%); border: 3px solid #10b981; border-radius: 10px; padding: 25px; position: relative;">
                        <div style="position: absolute; top: -12px; left: 20px; background: #10b981; color: white; padding: 4px 15px; border-radius: 20px; font-size: 12px; font-weight: 700;">EXPECTED</div>
                        <h3 style="margin: 15px 0 20px 0; font-size: 18px; font-weight: 800; color: #065f46; text-align: center;">Purchase Order</h3>
                       
                        <div style="background: white; border-radius: 8px; padding: 20px; margin-bottom: 15px;">
                            <div style="font-size: 13px; color: #6b7280; margin-bottom: 8px;">PO Number</div>
                            <div style="font-size: 20px; font-weight: 800; color: #065f46;">{po_number}</div>
                        </div>
                       
                        <div style="display: flex; justify-content: space-between; margin-bottom: 15px;">
                            <div>
                                <div style="font-size: 12px; color: #6b7280;">Quantity</div>
                                <div style="font-size: 18px; font-weight: 700; color: #065f46;">{po_qty} units</div>
                            </div>
                            <div>
                                <div style="font-size: 12px; color: #6b7280;">Unit Price</div>
                                <div style="font-size: 18px; font-weight: 700; color: #065f46;">${unit_price}</div>
                            </div>
                        </div>
                       
                        <div style="background: #10b981; color: white; padding: 12px; border-radius: 6px; text-align: center; font-weight: 700; font-size: 16px;">
                            Total: ${po_amount}
                        </div>
                    </div>
                   
                    <!-- Actual Box -->
                    <div style="background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%); border: 3px solid #dc2626; border-radius: 10px; padding: 25px; position: relative;">
                        <div style="position: absolute; top: -12px; left: 20px; background: #dc2626; color: white; padding: 4px 15px; border-radius: 20px; font-size: 12px; font-weight: 700;">INVOICED</div>
                        <h3 style="margin: 15px 0 20px 0; font-size: 18px; font-weight: 800; color: #991b1b; text-align: center;">Invoice Submitted</h3>
                       
                        <div style="background: white; border-radius: 8px; padding: 20px; margin-bottom: 15px;">
                            <div style="font-size: 13px; color: #6b7280; margin-bottom: 8px;">Invoice Number</div>
                            <div style="font-size: 20px; font-weight: 800; color: #991b1b;">{invoice_number}</div>
                        </div>
                       
                        <div style="display: flex; justify-content: space-between; margin-bottom: 15px;">
                            <div>
                                <div style="font-size: 12px; color: #6b7280;">Quantity</div>
                                <div style="font-size: 18px; font-weight: 700; color: #991b1b;">{invoice_qty} units</div>
                            </div>
                            <div>
                                <div style="font-size: 12px; color: #6b7280;">Unit Price</div>
                                <div style="font-size: 18px; font-weight: 700; color: #991b1b;">${invoice_unit_price}</div>
                            </div>
                        </div>
                       
                        <div style="background: #dc2626; color: white; padding: 12px; border-radius: 6px; text-align: center; font-weight: 700; font-size: 16px;">
                            Total: ${invoice_amount}
                        </div>
                    </div>
                </div>
               
                <!-- VISUAL MISMATCH INDICATORS -->
                <div style="background: #fffbeb; border: 2px dashed #f59e0b; border-radius: 10px; padding: 25px; margin-top: 30px;">
                    <h3 style="margin: 0 0 20px 0; font-size: 18px; font-weight: 700; color: #92400e; display: flex; align-items: center;">
                        <span style="background: #f59e0b; color: white; width: 28px; height: 28px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; margin-right: 12px; font-size: 16px;">↔️</span>
                        Visual Mismatch Indicators
                    </h3>
                   
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px;">
                        <div style="text-align: center;">
                            <div style="background: #fee2e2; width: 80px; height: 80px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 15px auto; border: 3px solid #dc2626;">
                                <span style="font-size: 28px; font-weight: 800; color: #dc2626;">+{qty_variance_percentage}%</span>
                            </div>
                            <div style="font-size: 14px; font-weight: 600; color: #374151;">Quantity Variance</div>
                            <div style="font-size: 12px; color: #6b7280;">Expected: {po_qty} → Actual: {invoice_qty}</div>
                        </div>
                       
                        <div style="text-align: center;">
                            <div style="background: #fee2e2; width: 80px; height: 80px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 15px auto; border: 3px solid #dc2626;">
                                <span style="font-size: 28px; font-weight: 800; color: #dc2626;">+{price_variance_percentage}%</span>
                            </div>
                            <div style="font-size: 14px; font-weight: 600; color: #374151;">Price Variance</div>
                            <div style="font-size: 12px; color: #6b7280;">Expected: ${unit_price} → Actual: ${invoice_unit_price}</div>
                        </div>
                       
                        <div style="text-align: center;">
                            <div style="background: #fee2e2; width: 80px; height: 80px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 15px auto; border: 3px solid #dc2626;">
                                <span style="font-size: 28px; font-weight: 800; color: #dc2626;">+{variance_percentage}%</span>
                            </div>
                            <div style="font-size: 14px; font-weight: 600; color: #374151;">Total Variance</div>
                            <div style="font-size: 12px; color: #6b7280;">${variance_amount} difference</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- DETAILED DISCREPANCY BREAKDOWN -->
        <div style="margin: 40px 0 30px 0;">
            <div style="background: white; border-radius: 12px; padding: 30px; box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);">
                <h2 style="margin: 0 0 25px 0; font-size: 22px; font-weight: 800; color: #111827; border-bottom: 3px solid #3b82f6; padding-bottom: 10px;">
                    Discrepancy Breakdown
                </h2>
               
                <!-- Discrepancy Table -->
                <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse: collapse;">
                    <thead>
                        <tr style="background: #f3f4f6;">
                            <th style="padding: 15px; text-align: left; font-size: 13px; font-weight: 700; color: #374151; border-bottom: 2px solid #d1d5db;">Field</th>
                            <th style="padding: 15px; text-align: left; font-size: 13px; font-weight: 700; color: #374151; border-bottom: 2px solid #d1d5db;">Expected</th>
                            <th style="padding: 15px; text-align: left; font-size: 13px; font-weight: 700; color: #374151; border-bottom: 2px solid #d1d5db;">Actual</th>
                            <th style="padding: 15px; text-align: left; font-size: 13px; font-weight: 700; color: #374151; border-bottom: 2px solid #d1d5db;">Variance</th>
                            <th style="padding: 15px; text-align: left; font-size: 13px; font-weight: 700; color: #374151; border-bottom: 2px solid #d1d5db;">Visual</th>
                        </tr>
                    </thead>
                    <tbody>
                        <!-- Quantity Row -->
                        <tr style="border-bottom: 1px solid #e5e7eb;">
                            <td style="padding: 18px 15px; font-weight: 600; color: #374151;">Quantity</td>
                            <td style="padding: 18px 15px; color: #059669; font-weight: 700;">{po_qty}</td>
                            <td style="padding: 18px 15px; color: #dc2626; font-weight: 700;">{invoice_qty}</td>
                            <td style="padding: 18px 15px; color: #f59e0b; font-weight: 700;">+{qty_variance}</td>
                            <td style="padding: 18px 15px;">
                                <div style="display: flex; align-items: center;">
                                    <div style="width: 100px; background: #d1fae5; height: 8px; border-radius: 4px; margin-right: 10px; overflow: hidden;">
                                        <div style="background: #10b981; height: 100%; width: 100%;"></div>
                                    </div>
                                    <div style="width: 110px; background: #fee2e2; height: 8px; border-radius: 4px; overflow: hidden;">
                                        <div style="background: #ef4444; height: 100%; width: 100%;"></div>
                                    </div>
                                </div>
                            </td>
                        </tr>
                       
                        <!-- Unit Price Row -->
                        <tr style="border-bottom: 1px solid #e5e7eb;">
                            <td style="padding: 18px 15px; font-weight: 600; color: #374151;">Unit Price</td>
                            <td style="padding: 18px 15px; color: #059669; font-weight: 700;">${unit_price}</td>
                            <td style="padding: 18px 15px; color: #dc2626; font-weight: 700;">${invoice_unit_price}</td>
                            <td style="padding: 18px 15px; color: #f59e0b; font-weight: 700;">+${price_variance}</td>
                            <td style="padding: 18px 15px;">
                                <div style="display: flex; align-items: center;">
                                    <div style="width: 100px; background: #d1fae5; height: 8px; border-radius: 4px; margin-right: 10px; overflow: hidden;">
                                        <div style="background: #10b981; height: 100%; width: 100%;"></div>
                                    </div>
                                    <div style="width: 113px; background: #fee2e2; height: 8px; border-radius: 4px; overflow: hidden;">
                                        <div style="background: #ef4444; height: 100%; width: 100%;"></div>
                                    </div>
                                </div>
                            </td>
                        </tr>
                       
                        <!-- Tax Row -->
                        <tr style="border-bottom: 1px solid #e5e7eb;">
                            <td style="padding: 18px 15px; font-weight: 600; color: #374151;">Tax Rate</td>
                            <td style="padding: 18px 15px; color: #059669; font-weight: 700;">{tax_rate}%</td>
                            <td style="padding: 18px 15px; color: #dc2626; font-weight: 700;">{invoice_tax}%</td>
                            <td style="padding: 18px 15px; color: #f59e0b; font-weight: 700;">+{tax_variance}%</td>
                            <td style="padding: 18px 15px;">
                                <div style="display: flex; align-items: center; justify-content: space-between;">
                                    <div style="width: 45%; text-align: center; background: #d1fae5; padding: 5px; border-radius: 4px; font-size: 12px; font-weight: 700; color: #065f46;">
                                        {tax_rate}%
                                    </div>
                                    <div style="color: #9ca3af; font-size: 12px;">→</div>
                                    <div style="width: 45%; text-align: center; background: #fee2e2; padding: 5px; border-radius: 4px; font-size: 12px; font-weight: 700; color: #991b1b;">
                                        {invoice_tax}%
                                    </div>
                                </div>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- RESOLUTION TIMELINE -->
        <div style="margin: 40px 0 30px 0;">
            <div style="background: white; border-radius: 12px; padding: 30px; box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);">
                <h2 style="margin: 0 0 25px 0; font-size: 22px; font-weight: 800; color: #111827; display: flex; align-items: center;">
                    <span style="background: #3b82f6; color: white; width: 36px; height: 36px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; margin-right: 12px; font-size: 18px;">⏰</span>
                    Resolution Timeline
                </h2>
               
                <!-- Timeline Visualization -->
                <div style="position: relative; padding-left: 30px; margin: 30px 0;">
                    <!-- Timeline Line -->
                    <div style="position: absolute; left: 15px; top: 0; bottom: 0; width: 4px; background: #3b82f6; border-radius: 2px;"></div>
                   
                    <!-- Today -->
                    <div style="position: relative; margin-bottom: 40px;">
                        <div style="position: absolute; left: -30px; top: 0; background: #3b82f6; width: 30px; height: 30px; border-radius: 50%; border: 4px solid white; box-shadow: 0 0 0 3px #3b82f6;"></div>
                        <div style="background: #eff6ff; padding: 20px; border-radius: 10px; margin-left: 20px; border: 2px solid #3b82f6;">
                            <div style="font-weight: 800; color: #1e40af; margin-bottom: 5px;">Today - Discrepancy Identified</div>
                            <div style="color: #6b7280; font-size: 14px;">Automated system detected {discrepancy_count} mismatches</div>
                        </div>
                    </div>
                   
                    <!-- Day 2 -->
                    <div style="position: relative; margin-bottom: 40px;">
                        <div style="position: absolute; left: -30px; top: 0; background: #f59e0b; width: 30px; height: 30px; border-radius: 50%; border: 4px solid white; box-shadow: 0 0 0 3px #f59e0b;"></div>
                        <div style="background: #fffbeb; padding: 20px; border-radius: 10px; margin-left: 20px; border: 2px solid #f59e0b;">
                            <div style="font-weight: 800; color: #92400e; margin-bottom: 5px;">Within 24 Hours - Acknowledgement Required</div>
                            <div style="color: #6b7280; font-size: 14px;">Vendor to acknowledge receipt and provide preliminary response</div>
                        </div>
                    </div>
                   
                    <!-- Day 5 -->
                    <div style="position: relative; margin-bottom: 40px;">
                        <div style="position: absolute; left: -30px; top: 0; background: #dc2626; width: 30px; height: 30px; border-radius: 50%; border: 4px solid white; box-shadow: 0 0 0 3px #dc2626;"></div>
                        <div style="background: #fef2f2; padding: 20px; border-radius: 10px; margin-left: 20px; border: 2px solid #dc2626;">
                            <div style="font-weight: 800; color: #991b1b; margin-bottom: 5px;">By {resolution_deadline} - Full Resolution Required</div>
                            <div style="color: #6b7280; font-size: 14px;">Submit corrected invoice or detailed explanation to avoid payment delays</div>
                        </div>
                    </div>
                   
                    <!-- Resolution -->
                    <div style="position: relative;">
                        <div style="position: absolute; left: -30px; top: 0; background: #10b981; width: 30px; height: 30px; border-radius: 50%; border: 4px solid white; box-shadow: 0 0 0 3px #10b981;"></div>
                        <div style="background: #ecfdf5; padding: 20px; border-radius: 10px; margin-left: 20px; border: 2px solid #10b981;">
                            <div style="font-weight: 800; color: #065f46; margin-bottom: 5px;">After Resolution - Payment Processing</div>
                            <div style="color: #6b7280; font-size: 14px;">Payment will be processed within 5 business days of discrepancy resolution</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- ACTION BUTTONS -->
        <div style="text-align: center; margin: 40px 0;">
            <a href="mailto:{reply_to_email}" style="display: inline-block; background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%); color: white; padding: 18px 45px; text-decoration: none; border-radius: 10px; font-weight: 800; font-size: 16px; box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4); margin: 0 10px; letter-spacing: 0.5px; border: none;">
                📧 Respond with Explanation
            </a>
            <a href="{portal_url}" style="display: inline-block; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 18px 45px; text-decoration: none; border-radius: 10px; font-weight: 800; font-size: 16px; box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4); margin: 0 10px; letter-spacing: 0.5px; border: none;">
                🔗 Upload Corrected Invoice
            </a>
        </div>

    </div>

    <!-- Footer -->
    <div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); color: #f1f5f9; padding: 30px 40px; text-align: center;">
        <div style="max-width: 600px; margin: 0 auto;">
            <div style="font-size: 24px; font-weight: 800; color: #ffffff; margin-bottom: 20px; letter-spacing: -0.5px;">{company_name}</div>
            <div style="font-size: 14px; color: #cbd5e1; margin-bottom: 25px; line-height: 1.6;">
                This visual discrepancy report was automatically generated by our AP Automation System.<br>
                For assistance, contact {reply_to_email} or call {company_contact}
            </div>
            <div style="border-top: 1px solid #334155; padding-top: 20px; font-size: 12px; color: #94a3b8;">
                Reference: {reference_number} |
                Generated: {generation_date} |
                System: AP Automation v3.2
            </div>
        </div>
    </div>

</div>'''

        # Generate simple plain text version
        plain_text = f"""
INVOICE DISCREPANCY ALERT
Visual Discrepancy Analysis Report

QUICK SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Invoice Amount:  ${invoice_amount}
PO Amount:       ${po_amount}
Variance:        ${variance_amount}


VISUAL DISCREPANCY ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

AMOUNT COMPARISON
Expected (PO):      ${po_amount} [████████████████████] 100%
Invoice Submitted:  ${invoice_amount} [█████████████████████████] {invoice_percentage}%

PURCHASE ORDER (EXPECTED)
  PO Number:    {po_number}
  Quantity:     {po_qty} units
  Unit Price:   ${unit_price}
  Total:        ${po_amount}

INVOICE SUBMITTED
  Invoice No:   {invoice_number}
  Quantity:     {invoice_qty} units
  Unit Price:   ${invoice_unit_price}
  Total:        ${invoice_amount}

VARIANCE INDICATORS
  Quantity Variance:  +{qty_variance_percentage}% (Expected: {po_qty} → Actual: {invoice_qty})
  Price Variance:     +{price_variance_percentage}% (Expected: ${unit_price} → Actual: ${invoice_unit_price})
  Total Variance:     +{variance_percentage}% (${variance_amount} difference)


DISCREPANCY BREAKDOWN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Field          Expected      Actual        Variance
─────────────────────────────────────────────────
Quantity       {po_qty}          {invoice_qty}          +{qty_variance}
Unit Price     ${unit_price}     ${invoice_unit_price}  +${price_variance}
Tax Rate       {tax_rate}%       {invoice_tax}%         +{tax_variance}%


RESOLUTION TIMELINE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
○ Today - Discrepancy Identified
  Automated system detected {discrepancy_count} mismatches

○ Within 24 Hours - Acknowledgement Required
  Vendor to acknowledge receipt and provide preliminary response

○ By {resolution_deadline} - Full Resolution Required
  Submit corrected invoice or detailed explanation to avoid payment delays

○ After Resolution - Payment Processing
  Payment will be processed within 5 business days of discrepancy resolution


ACTIONS REQUIRED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Reply with explanation: {reply_to_email}
• Upload corrected invoice: {portal_url}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{company_name}
This visual discrepancy report was automatically generated by our AP Automation System.
For assistance, contact {reply_to_email} or call {company_contact}

Reference: {reference_number} | Generated: {generation_date} | System: AP Automation v3.2
"""
        
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
