"""
Email Processor Agent - AI-powered Email Generator and Analyser

This package provides:
- Email Generator: Create professional email drafts using AI
- Email Analyser: Analyze incoming emails and generate intelligent responses
- IMAP Client: Connect to Gmail via IMAP for reading emails
- SMTP Client: Send emails via Gmail SMTP
- Approval Workflow: CFO approval before sending to final recipient
"""

__version__ = "1.0.0"
__author__ = "Email Processor Agent"

from email_processor.config import Settings
from email_processor.models import EmailMessage, EmailDraft, EmailAnalysis
from email_processor.approval_workflow import ApprovalWorkflow, ApprovalRequest, ApprovalStatus

__all__ = [
    "Settings",
    "EmailMessage",
    "EmailDraft",
    "EmailAnalysis",
    "ApprovalWorkflow",
    "ApprovalRequest",
    "ApprovalStatus",
]
