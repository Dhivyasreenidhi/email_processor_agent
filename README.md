# Email Processor Agent

🤖 AI-powered Email Processor Agent with Email Generator and Email Analyser capabilities using IMAP/SMTP with Gmail.

## Features

### 📧 Email Generator
- Generate professional email drafts using AI (Google Gemini)
- Multiple email types: introductions, follow-ups, general purpose
- Customizable tone (professional, friendly, formal, casual)
- Automatic subject line generation

### 🔍 Email Analyser
- Analyze incoming emails for:
  - **Category**: inquiry, complaint, feedback, support, sales, etc.
  - **Priority**: urgent, high, normal, low
  - **Sentiment**: positive, neutral, negative
  - **Key Points**: Extract main topics
  - **Actions Required**: Determine if response needed
- Generate intelligent responses based on analysis

### 📥 IMAP Client
- Connect to Gmail via IMAP
- Fetch unread/all emails
- Search emails by criteria
- Mark as read/unread
- Move between folders

### 📤 SMTP Client
- Send emails via Gmail SMTP
- Support for attachments
- HTML and plain text emails
- Reply threading support

## Installation

### Prerequisites
- Python 3.10+
- Gmail account with App Password enabled
- Google AI API key (Gemini)

### Setup

1. Clone or navigate to the project directory:
```bash
cd email-processor-agent
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the package:
```bash
pip install -e .
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your credentials
```

### Gmail App Password Setup

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable 2-Step Verification if not already enabled
3. Go to [App Passwords](https://myaccount.google.com/apppasswords)
4. Create a new App Password for "Mail"
5. Copy the 16-character password to your `.env` file

### Google AI API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy to your `.env` file as `GOOGLE_API_KEY`

## Usage

### CLI Commands

```bash
# Show configuration
email-agent config

# Fetch unread emails
email-agent fetch --limit 10

# Analyze unread emails
email-agent analyze --limit 5

# Generate a new email
email-agent generate "Schedule a meeting for next week" \
  --to recipient@example.com \
  --name "John Doe" \
  --tone professional \
  --signature "Your Name"

# Generate a follow-up email
email-agent follow-up "Project Proposal" \
  --context "Sent proposal for the new project" \
  --to recipient@example.com \
  --days 7

# Process inbox (analyze + generate responses)
email-agent process --limit 10

# Run in continuous polling mode
email-agent poll --interval 60

# Interactive mode
email-agent interactive
```

### Python API

```python
from email_processor import Settings
from email_processor.agent import EmailProcessorAgent

# Initialize agent
agent = EmailProcessorAgent()

# Fetch unread emails
emails = agent.fetch_unread_emails(limit=5)

# Analyze an email
for email in emails:
    analysis = agent.analyze_email(email)
    print(f"Category: {analysis.category}")
    print(f"Sentiment: {analysis.sentiment}")
    print(f"Summary: {analysis.summary}")
    
    # Generate response if needed
    if analysis.action_required:
        response = agent.suggest_response(email, analysis)
        print(f"Response: {response.body_text}")
        
        # Send the response
        # agent.send_email(response)

# Generate a new email
draft = agent.generate_email(
    purpose="Request a meeting to discuss Q4 results",
    recipient_email="colleague@company.com",
    recipient_name="John",
    tone="professional",
    signature_name="Your Name"
)
print(f"Subject: {draft.subject}")
print(f"Body: {draft.body_text}")

# Send the email
# agent.send_email(draft)
```

### Event Callbacks

```python
from email_processor.agent import EmailProcessorAgent

agent = EmailProcessorAgent()

# Register callbacks
@agent.on_email_received
def handle_new_email(email):
    print(f"New email: {email.subject}")

@agent.on_email_analyzed
def handle_analysis(email, analysis):
    print(f"Analyzed: {analysis.category.value}")

@agent.on_response_generated
def handle_response(email, draft):
    print(f"Response ready: {draft.subject}")

# Run polling mode
agent.run_polling(auto_respond=False)
```

## Project Structure

```
email-processor-agent/
├── src/
│   └── email_processor/
│       ├── __init__.py          # Package exports
│       ├── config.py            # Settings management
│       ├── models.py            # Data models
│       ├── imap_client.py       # Gmail IMAP client
│       ├── smtp_client.py       # Gmail SMTP client
│       ├── email_generator.py   # AI email generator
│       ├── email_analyser.py    # AI email analyser
│       ├── agent.py             # Main orchestrator
│       └── cli.py               # CLI interface
├── tests/                       # Test files
├── templates/                   # Email templates (optional)
├── .env.example                 # Environment template
├── pyproject.toml              # Project configuration
└── README.md                   # This file
```

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `GMAIL_EMAIL` | Your Gmail address | Required |
| `GMAIL_APP_PASSWORD` | Gmail App Password | Required |
| `GOOGLE_API_KEY` | Google AI API Key | Required |
| `IMAP_SERVER` | IMAP server | imap.gmail.com |
| `IMAP_PORT` | IMAP port | 993 |
| `SMTP_SERVER` | SMTP server | smtp.gmail.com |
| `SMTP_PORT` | SMTP port | 587 |
| `POLL_INTERVAL_SECONDS` | Polling interval | 60 |
| `MAX_EMAILS_PER_BATCH` | Max emails per batch | 10 |
| `AUTO_RESPOND` | Auto-send responses | false |
| `LOG_LEVEL` | Logging level | INFO |

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src tests
isort src tests

# Type checking
mypy src
```

## Security Notes

- **Never commit your `.env` file** - it contains sensitive credentials
- Use Gmail App Passwords, not your main password
- The `AUTO_RESPOND` setting is `false` by default for safety
- Review generated responses before sending in production

## License

MIT License
