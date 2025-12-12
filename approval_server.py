#!/usr/bin/env python3
"""
Email Approval Web Server
Provides a web UI for CFO to approve/reject emails.
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import json
import os
from datetime import datetime
from pathlib import Path
import logging

from email_processor.config import get_settings
from email_processor.approval_workflow import ApprovalWorkflow, ApprovalRequest
from email_processor.models import EmailDraft, EmailAddress

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='ui')
CORS(app)

PENDING_APPROVALS_FILE = Path(__file__).parent / "pending_approvals.json"
CFO_EMAIL = "arunsukumar03@gmail.com"

def load_pending_approvals():
    """Load pending approvals from JSON file."""
    if not PENDING_APPROVALS_FILE.exists():
        return []
    
    try:
        with open(PENDING_APPROVALS_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading pending approvals: {e}")
        return []

def save_pending_approvals(approvals):
    """Save pending approvals to JSON file."""
    try:
        with open(PENDING_APPROVALS_FILE, 'w') as f:
            json.dump(approvals, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving pending approvals: {e}")

@app.route('/')
def index():
    """Serve the main UI."""
    return send_from_directory('ui', 'approval.html')

@app.route('/styles.css')
def styles():
    """Serve the CSS file."""
    return send_from_directory('ui', 'styles.css')

@app.route('/app.js')
def app_js():
    """Serve the JavaScript file."""
    return send_from_directory('ui', 'app.js')

@app.route('/api/pending')
def get_pending():
    """Get all pending approval requests."""
    approvals = load_pending_approvals()
    pending = [a for a in approvals if a['status'] == 'pending']
    
    # Add stats
    total = len(approvals)
    approved = len([a for a in approvals if a['status'] == 'approved'])
    rejected = len([a for a in approvals if a['status'] == 'rejected'])
    
    return jsonify({
        'pending': pending,
        'stats': {
            'total': total,
            'pending': len(pending),
            'approved': approved,
            'rejected': rejected
        }
    })

@app.route('/api/pending-approvals')
def get_pending_approvals():
    """Get all pending approval requests formatted for the UI."""
    approvals = load_pending_approvals()
    pending = [a for a in approvals if a['status'] == 'pending']
    
    # Format bills for the UI
    bills = []
    for approval in pending:
        # Extract vendor name from final_recipient_name or email
        vendor_name = approval.get('final_recipient_name', approval.get('final_recipient_email', 'Unknown Vendor'))
        
        # Parse discrepancies from email content
        discrepancies = []
        email_body = approval.get('draft_body', '')
        if 'discrepancy' in email_body.lower() or 'mismatch' in email_body.lower():
            # This is a discrepancy email
            discrepancies.append({
                'type': 'Discrepancy Detected',
                'title': 'Invoice/PO Mismatch',
                'details': 'Review required for vendor communication'
            })
        
        # Parse amount if available (default to random for demo)
        import random
        amount = random.randint(1000, 15000)
        
        bill = {
            'id': approval['request_id'],
            'vendor': vendor_name,
            'vendor_email': approval.get('final_recipient_email', ''),
            'amount': amount,
            'status': 'Pending Review',
            'emailStatus': 'Awaiting Approval',
            'date': approval.get('created_at', '')[:10],  # Just the date part
            'request_id': approval['request_id'],
            'discrepancies': discrepancies,
            'emailContent': {
                'greeting': f"Dear {vendor_name} Team,",
                'intro': 'We have reviewed your recent submission and would like to communicate the following:',
                'discrepancySummary': discrepancies,
                'requestItems': [
                    'Please review the details in the email below',
                    'Respond with any corrections or clarifications',
                    'Confirm receipt and expected timeline'
                ],
                'warning': 'This email requires CFO approval before sending',
                'htmlBody': approval.get('draft_body_html', approval.get('draft_body', '')),  # Include HTML body
                'plainBody': approval.get('draft_body', '')
            }
        }
        bills.append(bill)
    
    return jsonify({
        'bills': bills,
        'stats': {
            'total': len(approvals),
            'pending': len(pending),
            'approved': len([a for a in approvals if a['status'] == 'approved']),
            'rejected': len([a for a in approvals if a['status'] == 'rejected'])
        }
    })

@app.route('/api/approve/<request_id>', methods=['POST'])
def approve_email(request_id):
    """Approve an email and send it to the vendor."""
    try:
        approvals = load_pending_approvals()
        request_data = None
        
        # Find the request
        for approval in approvals:
            if approval['request_id'] == request_id:
                request_data = approval
                break
        
        if not request_data:
            return jsonify({'error': 'Request not found'}), 404
        
        if request_data['status'] != 'pending':
            return jsonify({'error': 'Request already processed'}), 400
        
        # Get settings and create workflow
        settings = get_settings()
        workflow = ApprovalWorkflow(settings=settings, approver_email=CFO_EMAIL)
        
        # Reconstruct the approval request WITH HTML body
        draft = EmailDraft(
            to=[EmailAddress(email=email) for email in request_data['draft_to']],
            subject=request_data['draft_subject'],
            body_text=request_data['draft_body'],
            body_html=request_data.get('draft_body_html')  # Include HTML body!
        )
        
        approval_req = ApprovalRequest(
            request_id=request_data['request_id'],
            draft=draft,
            final_recipient=EmailAddress(
                email=request_data['final_recipient_email'],
                name=request_data['final_recipient_name']
            ),
            approver_email=request_data['approver_email'],
            approval_message_id=request_data['approval_message_id'],
            created_at=datetime.fromisoformat(request_data['created_at'])
        )
        
        # Log HTML info
        has_html = draft.body_html and len(draft.body_html.strip()) > 0
        logger.info(f"Approving email for {request_data['final_recipient_email']} with HTML: {has_html}")
        if has_html:
            logger.info(f"HTML body length: {len(draft.body_html)} characters")
        
        # Send the email to vendor using the workflow's method
        logger.info(f"Sending approved email to {request_data['final_recipient_email']}")
        approval_req.status = 'approved'
        approval_req.approved_at = datetime.now()
        workflow._send_final_email(approval_req)
        
        # Update status in our JSON file
        request_data['status'] = 'approved'
        request_data['approved_at'] = datetime.now().isoformat()
        request_data['sent_at'] = datetime.now().isoformat()
        
        save_pending_approvals(approvals)
        
        return jsonify({
            'success': True,
            'message': f"Email approved and sent to {request_data['final_recipient_email']}",
            'request': request_data
        })
        
    except Exception as e:
        logger.error(f"Error approving email: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/approve', methods=['POST'])
def approve_from_ui():
    """Approve an email from the UI (without request_id in URL)."""
    try:
        data = request.get_json()
        bill_id = data.get('bill_id') or data.get('request_id')
        
        if not bill_id:
            return jsonify({'error': 'Missing bill_id or request_id'}), 400
        
        # Call the existing approve_email function
        return approve_email(bill_id)
        
    except Exception as e:
        logger.error(f"Error in approve_from_ui: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/reject/<request_id>', methods=['POST'])
def reject_email(request_id):
    """Reject an email."""
    try:
        data = request.get_json()
        reason = data.get('reason', 'No reason provided')
        
        approvals = load_pending_approvals()
        request_data = None
        
        # Find the request
        for approval in approvals:
            if approval['request_id'] == request_id:
                request_data = approval
                break
        
        if not request_data:
            return jsonify({'error': 'Request not found'}), 404
        
        if request_data['status'] != 'pending':
            return jsonify({'error': 'Request already processed'}), 400
        
        # Update status
        request_data['status'] = 'rejected'
        request_data['rejected_at'] = datetime.now().isoformat()
        request_data['notes'] = reason
        
        save_pending_approvals(approvals)
        
        return jsonify({
            'success': True,
            'message': 'Email rejected',
            'request': request_data
        })
        
    except Exception as e:
        logger.error(f"Error rejecting email: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/reject', methods=['POST'])
def reject_from_ui():
    """Reject an email from the UI (without request_id in URL)."""
    try:
        data = request.get_json()
        bill_id = data.get('bill_id') or data.get('request_id')
        reason = data.get('reason', 'No reason provided')
        
        if not bill_id:
            return jsonify({'error': 'Missing bill_id or request_id'}), 400
        
        # Process rejection directly here instead of calling reject_email
        approvals = load_pending_approvals()
        request_data = None
        
        # Find the request
        for approval in approvals:
            if approval['request_id'] == bill_id:
                request_data = approval
                break
        
        if not request_data:
            return jsonify({'error': 'Request not found'}), 404
        
        if request_data['status'] != 'pending':
            return jsonify({'error': 'Request already processed'}), 400
        
        # Update status
        request_data['status'] = 'rejected'
        request_data['rejected_at'] = datetime.now().isoformat()
        request_data['notes'] = reason
        
        save_pending_approvals(approvals)
        
        return jsonify({
            'success': True,
            'message': 'Email rejected',
            'request': request_data
        })
        
    except Exception as e:
        logger.error(f"Error in reject_from_ui: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting Email Approval Server...")
    print(f"📧 CFO Email: {CFO_EMAIL}")
    print(f"📁 Approvals file: {PENDING_APPROVALS_FILE}")
    print(f"🌐 Server running at: http://localhost:5000")
    print()
    
    app.run(debug=True, port=5000, host='0.0.0.0')
