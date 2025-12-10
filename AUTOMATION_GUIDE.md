# Email Automation Quick Start Guide

## 🚀 Automated Workflow

The `automation.py` script combines everything into one automated process:
1. **Generates** 10 test emails (5 discrepancy + 5 regular)
2. **Submits** them to CFO for approval
3. **Monitors** for approval responses in real-time
4. **Sends** approved emails to vendor automatically

## Usage

### Basic Usage (Default 1-second interval)
```bash
./venv/bin/python automation.py
```

### Custom Check Interval
```bash
# Check every 5 seconds
./venv/bin/python automation.py --interval 5

# Check every 10 seconds
./venv/bin/python automation.py --interval 10
```

## What Happens

1. **Email Generation**: AI generates professional emails based on templates
2. **Approval Submission**: All emails sent to CFO (arunsukumar03@gmail.com) for approval
3. **Real-time Monitoring**: System checks CFO's inbox every 1 second (or your chosen interval)
4. **Auto-Send**: When CFO replies "APPROVED", email automatically goes to vendor

## Stop the Automation

Press `Ctrl+C` at any time to stop the monitoring

## Workflow Participants

- **CFO (Approver)**: arunsukumar03@gmail.com
- **Vendor (Final Recipient)**: dhivyasreenidhidurai@gmail.com

## Example Run

```bash
# Simple one-command automation
./venv/bin/python automation.py
```

This will:
- ✅ Generate 10 emails with AI
- ✅ Submit all to CFO for approval  
- ✅ Start monitoring immediately
- ✅ Auto-send when approved
