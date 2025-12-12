"""
Guardrails AI integration for Email Auto-Responder.

This module provides validation and safety checks for email responses.
Uses Pydantic for structured validation with business rules.
"""

from typing import Optional, Tuple
from pydantic import BaseModel, Field, field_validator, ValidationError
import logging

logger = logging.getLogger(__name__)


class EmailResponseValidation(BaseModel):
    """Pydantic model for email response validation with business rules."""
    
    subject: str = Field(
        description="Email subject line",
        min_length=5,
        max_length=200
    )
    
    body: str = Field(
        description="Email body content - must be concise and professional",
        min_length=20,
        max_length=1000
    )
    
    @field_validator('body')
    @classmethod
    def validate_conciseness(cls, v: str) -> str:
        """Enforce concise responses (< 150 words)."""
        word_count = len(v.split())
        if word_count > 150:
            raise ValueError(
                f"Response too long ({word_count} words). "
                f"Must be under 150 words for conciseness."
            )
        return v
    
    @field_validator('body')
    @classmethod
    def validate_no_sensitive_info(cls, v: str) -> str:
        """Ensure no sensitive information in response."""
        sensitive_keywords = [
            'password', 'passwd', 'pwd',
            'ssn', 'social security',
            'credit card', 'cvv', 'card number',
            'bank account', 'routing number',
            'api key', 'api_key', 'apikey',
            'secret', 'private key', 'token',
            'confidential', 'classified'
        ]
        
        v_lower = v.lower()
        for keyword in sensitive_keywords:
            if keyword in v_lower:
                raise ValueError(
                    f"Response contains potentially sensitive information: '{keyword}'"
                )
        return v
    
    @field_validator('body')
    @classmethod
    def validate_professional_language(cls, v: str) -> str:
        """Ensure professional language (no profanity)."""
        unprofessional_words = [
            'damn', 'dammit', 'hell', 'crap',
            'stupid', 'idiot', 'dumb', 'moron',
            'sucks', 'screw', 'pissed'
        ]
        
        v_lower = v.lower()
        words_in_text = set(v_lower.split())
        
        for word in unprofessional_words:
            if word in words_in_text:
                raise ValueError(
                    f"Response contains unprofessional language: '{word}'"
                )
        return v
    
    @field_validator('body')
    @classmethod
    def validate_no_placeholders(cls, v: str) -> str:
        """Ensure no placeholder text remains."""
        placeholders = [
            '[INSERT', '[COMPANY', '[NAME]', '[EMAIL]',
            'TODO', 'FIXME', 'TBD', 'XXX',
            '{{', '}}', '<insert>', '<replace>'
        ]
        
        for placeholder in placeholders:
            if placeholder.lower() in v.lower():
                raise ValueError(
                    f"Response contains placeholder text: '{placeholder}'"
                )
        return v
    
    @field_validator('subject')
    @classmethod
    def validate_subject(cls, v: str) -> str:
        """Validate subject line."""
        if len(v.split()) < 2:
            raise ValueError("Subject must contain at least 2 words")
        
        if v.isupper() and len(v) > 10:
            raise ValueError("Subject should not be all uppercase")
        
        return v


def validate_email_response(
    subject: str,
    body: str
) -> Tuple[bool, Optional[str]]:
    """
    Validate email response using Pydantic validators.
    
    Args:
        subject: Email subject line
        body: Email body content
        
    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if validation passed
        - error_message: Error description if validation failed, None otherwise
    """
    try:
        # Validate using Pydantic model
        EmailResponseValidation(subject=subject, body=body)
        logger.info("✅ Email response validation passed")
        return True, None
        
    except ValidationError as e:
        # Extract first error message
        error_msg = e.errors()[0]['msg']
        logger.warning(f"⚠️  Validation failed: {error_msg}")
        return False, error_msg
    except Exception as e:
        error_msg = f"Unexpected validation error: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return False, error_msg


def quick_safety_check(text: str) -> Tuple[bool, str]:
    """
    Quick safety check without full validation.
    
    Args:
        text: Text to check
        
    Returns:
        Tuple of (is_safe, message)
    """
    # Length check
    if len(text) > 1000:
        return False, f"⚠️  Text too long ({len(text)} chars, max: 1000)"
    
    # Word count check
    word_count = len(text.split())
    if word_count > 150:
        return False, f"⚠️  Too wordy ({word_count} words, max: 150)"
    
    # Sensitive info check
    sensitive_patterns = [
        ('password', "Contains 'password'"),
        ('ssn', "Contains 'SSN'"),
        ('credit card', "Contains 'credit card'"),
        ('api key', "Contains 'API key'"),
        ('secret', "Contains 'secret'"),
        ('confidential', "Contains 'confidential'"),
    ]
    
    text_lower = text.lower()
    for pattern, reason in sensitive_patterns:
        if pattern in text_lower:
            return False, f"⚠️  {reason}"
    
    # Placeholder check
    placeholders = ['{{', '}}', '[INSERT', '[NAME]', 'TODO', 'FIXME']
    for placeholder in placeholders:
        if placeholder in text:
            return False, f"⚠️  Contains placeholder: {placeholder}"
    
    return True, "✅ All safety checks passed"


# Example usage and tests
if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("🛡️  GUARDRAILS EMAIL VALIDATOR TESTS")
    print("=" * 60)
    
    # Test 1: Valid response
    print("\n✅ Test 1: Valid response")
    is_valid, error = validate_email_response(
        subject="Re: Invoice Discrepancy INV-2024-123",
        body="Dear John,\n\nPlease review invoice INV-2024-305 and provide the correct unit price.\n\nBest regards,\nGenWorx Team"
    )
    print(f"   Valid: {is_valid}")
    if error:
        print(f"   Error: {error}")
    
    # Test 2: Too long (>150 words)
    print("\n❌ Test 2: Response too long (>150 words)")
    long_body = " ".join(["word"] * 200)
    is_valid, error = validate_email_response(
        subject="Re: Test Message",
        body=long_body
    )
    print(f"   Valid: {is_valid}")
    print(f"   Error: {error}")
    
    # Test 3: Contains sensitive info
    print("\n❌ Test 3: Contains sensitive information")
    is_valid, error = validate_email_response(
        subject="Re: Account Access",
        body="Your password is 12345. Please use this API key to access the system."
    )
    print(f"   Valid: {is_valid}")
    print(f"   Error: {error}")
    
    # Test 4: Contains placeholder
    print("\n❌ Test 4: Contains placeholder text")
    is_valid, error = validate_email_response(
        subject="Re: Information Request",
        body="Dear [INSERT NAME],\n\nPlease contact us at [EMAIL] for more information."
    )
    print(f"   Valid: {is_valid}")
    print(f"   Error: {error}")
    
    # Test 5: Unprofessional language
    print("\n❌ Test 5: Unprofessional language")
    is_valid, error = validate_email_response(
        subject="Re: Your Request",
        body="This is stupid. You should know better than to ask such dumb questions."
    )
    print(f"   Valid: {is_valid}")
    print(f"   Error: {error}")
    
    # Test 6: Subject too short
    print("\n❌ Test 6: Subject too short")
    is_valid, error = validate_email_response(
        subject="Re",
        body="Dear Customer, Thank you for your inquiry. We will get back to you soon."
    )
    print(f"   Valid: {is_valid}")
    print(f"   Error: {error}")
    
    # Test 7: Quick safety check
    print("\n✅ Test 7: Quick safety check (valid)")
    is_safe, msg = quick_safety_check(
        "Dear John, Please provide clarification on invoice INV-123. Best regards, Team"
    )
    print(f"   Safe: {is_safe}")
    print(f"   Message: {msg}")
    
    # Test 8: Quick safety check (invalid - too long)
    print("\n❌ Test 8: Quick safety check (too long)")
    is_safe, msg = quick_safety_check(" ".join(["word"] * 200))
    print(f"   Safe: {is_safe}")
    print(f"   Message: {msg}")
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)
