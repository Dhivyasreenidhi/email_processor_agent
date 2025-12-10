"""
Configuration management for Email Processor Agent.

Uses pydantic-settings for environment variable management with validation.
"""

from pathlib import Path
from typing import Optional

from pydantic import Field, EmailStr, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Gmail Credentials
    gmail_email: EmailStr = Field(
        ...,
        description="Gmail email address for authentication",
    )
    gmail_app_password: SecretStr = Field(
        ...,
        description="Gmail App Password (not regular password)",
    )

    # IMAP Configuration
    imap_server: str = Field(
        default="imap.gmail.com",
        description="IMAP server hostname",
    )
    imap_port: int = Field(
        default=993,
        description="IMAP server port",
    )
    imap_use_ssl: bool = Field(
        default=True,
        description="Use SSL for IMAP connection",
    )

    # SMTP Configuration
    smtp_server: str = Field(
        default="smtp.gmail.com",
        description="SMTP server hostname",
    )
    smtp_port: int = Field(
        default=587,
        description="SMTP server port",
    )
    smtp_use_tls: bool = Field(
        default=True,
        description="Use TLS for SMTP connection",
    )

    # Google AI Configuration
    google_api_key: SecretStr = Field(
        ...,
        description="Google AI (Gemini) API Key",
    )

    # Agent Configuration
    poll_interval_seconds: int = Field(
        default=60,
        ge=10,
        description="Interval between email checks in seconds",
    )
    max_emails_per_batch: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum emails to process per batch",
    )
    auto_respond: bool = Field(
        default=False,
        description="Automatically send responses (use with caution)",
    )
    log_level: str = Field(
        default="INFO",
        pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$",
        description="Logging level",
    )

    # Templates Configuration
    templates_dir: Optional[Path] = Field(
        default=None,
        description="Directory for email templates",
    )

    @property
    def imap_connection_string(self) -> str:
        """Get formatted IMAP connection info."""
        protocol = "imaps" if self.imap_use_ssl else "imap"
        return f"{protocol}://{self.imap_server}:{self.imap_port}"

    @property
    def smtp_connection_string(self) -> str:
        """Get formatted SMTP connection info."""
        protocol = "smtps" if self.smtp_use_tls else "smtp"
        return f"{protocol}://{self.smtp_server}:{self.smtp_port}"


def get_settings() -> Settings:
    """Get application settings singleton."""
    return Settings()
