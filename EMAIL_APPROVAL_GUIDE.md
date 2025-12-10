# Email Approval System - Complete Guide

## 🎯 Overview

This system allows automated email generation with CFO approval workflow. Emails are generated, sent to CFO for review via a beautiful web UI, and upon approval, automatically sent to vendors.

---

## 📧 Complete Workflow

### **Step 1: Generate & Submit Emails**
```bash
./venv/bin/python automation.py
```

This script:
- ✅ Generates 10 emails (5 discrepancy + 5 regular)
- ✅ Submits them for CFO approval
- ✅ Saves to `pending_approvals.json`
- ✅ Starts monitoring for approval responses

### **Step 2: CFO Reviews in Web UI**

Open: **http://localhost:5000**

The UI features:
- 📊 **Bills List**: Shows all pending emails
- 📝 **Detail Panel**: Email content preview
- ✅ **Approve & Send**: Sends email to vendor
- ❌ **Reject**: Removes the email (won't be sent)
- ✏️ **Edit Email**: Modify content before approving

---

## 🖥️ Using the Web UI

### **Approving an Email**

1. **Click on a bill** in the left panel to view details
2. **Click "Review Email"** to open the modal
3. **Review the email content**:
   - Vendor information
   - Discrepancies found
   - Email content (editable)
4. **Click "Approve & Send Email"**:
   - ⏳ Button shows loading spinner: "Sending Email..."
   - ✅ Success state: "Email Sent!"
   - 🎉 Email is sent to vendor
   - 🗑️ Removed from pending list

### **Rejecting an Email**

1. **Click on a bill** in the left panel
2. **Click "Reject"** button
3. **Confirm the rejection** in the dialog:
   ```
   Are you sure you want to reject this email?
   
   Vendor: [Vendor Name]
   Amount: $[Amount]
   
   This email will NOT be sent to the vendor.
   ```
4. **Optional**: Provide a rejection reason
5. ✅ Email is rejected and removed from the list

---

## 🎨 Features

### **Loading States**
- ⏳ **Approve Button**: Shows spinning animation while sending
- 🔒 **Disabled Buttons**: Prevents double-clicks during processing
- ✅ **Success Animation**: Brief success state before closing modal

### **Professional Email Templates (Jinja2)**

Located in `/templates`:
- `discrepancy_email.html` - For invoice/PO discrepancies
- `regular_email.html` - For general business communication

**Features**:
- Beautiful HTML formatting with gradients
- Mobile-responsive design
- Professional styling
- Plain text fallback included

---

## 📁 Project Structure

```
email-processor-agent/
├── ui/
│   ├── approval.html          # Main UI page
│   ├── styles.css             # Premium styling
│   └── app.js                 # UI logic + API calls
├── templates/
│   ├── discrepancy_email.html # Jinja2 template
│   └── regular_email.html     # Jinja2 template
├── src/email_processor/
│   ├── email_templates.py     # Template renderer
│   ├── email_generator.py     # AI email generation
│   ├── approval_workflow.py   # Approval logic
│   └── smtp_client.py         # Email sending
├── approval_server.py         # Flask API server
├── automation.py              # Complete workflow
├── pending_approvals.json     # Current pending emails
└── demo_jinja2_templates.py   # Template demo
```

---

## 🔧 API Endpoints

### **GET /api/pending-approvals**
Returns all pending approval requests formatted for the UI.

**Response:**
```json
{
  "bills": [...],
  "stats": {
    "total": 19,
    "pending": 19,
    "approved": 0,
    "rejected": 0
  }
}
```

### **POST /api/approve**
Approves and sends an email to the vendor.

**Request:**
```json
{
  "bill_id": "ABC123DEF456",
  "request_id": "ABC123DEF456",
  "email_content": "<html>...</html>",
  "vendor_email": "vendor@example.com"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Email approved and sent to vendor@example.com"
}
```

### **POST /api/reject**
Rejects an email (won't be sent).

**Request:**
```json
{
  "bill_id": "ABC123DEF456",
  "reason": "Needs more review"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Email rejected"
}
```

---

## 🚀 Quick Start

### **1. Start the Approval Server**
```bash
./venv/bin/python approval_server.py
```

### **2. Generate Test Emails**
```bash
./venv/bin/python automation.py
```

### **3. Open the UI**
Open browser: **http://localhost:5000**

### **4. Approve or Reject Emails**
Use the beautiful web interface!

---

## 🎯 Demo: Jinja2 Templates

To see the beautiful email templates:

```bash
./venv/bin/python demo_jinja2_templates.py
```

This generates sample emails in `email_outputs/`:
- `discrepancy_email.html` - Open in browser to see
- `regular_email.html` - Open in browser to see

---

## 💡 Key Features

✅ **Beautiful UI** with modern design  
✅ **Loading animations** for better UX  
✅ **Jinja2 email templates** for professional emails  
✅ **Edit emails** before sending  
✅ **Reject with confirmation** to prevent mistakes  
✅ **Real-time updates** - bills removed instantly  
✅ **Mobile responsive** design  
✅ **Two approval methods**:
   - Web UI (recommended)
   - Email reply with "APPROVED" or "REJECTED"

---

## 📝 Environment Variables

Required in `.env`:
```bash
# Google API
GOOGLE_API_KEY=your_api_key_here

# Email Configuration
GMAIL_USER=your_email@gmail.com
GMAIL_APP_PASSWORD=your_app_password

# Email Addresses
CFO_EMAIL=arunsukumar03@gmail.com
VENDOR_EMAIL=dhivyasreenidhidurai@gmail.com
```

---

## 🎨 UI Customization

Edit `ui/styles.css` to customize:
- Colors (primary, accent, status)
- Spacing
- Animations
- Button styles
- Modal appearance

---

## 🔄 Workflow States

```
┌─────────────┐
│  Generated  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Pending   │ ← You are here (in UI)
└──────┬──────┘
       │
    ┌──┴──┐
    │     │
    ▼     ▼
┌────────┐ ┌──────────┐
│Approved│ │ Rejected │
└───┬────┘ └──────────┘
    │           │
    ▼           ▼
┌────────┐ ┌──────────┐
│  Sent  │ │ Removed  │
└────────┘ └──────────┘
```

---

## 🌟 Tips

1. **Refresh the page** to see newly generated emails
2. **Use the search bar** to filter bills
3. **Edit emails** if you need to modify content
4. **Check rejection reason** by providing meaningful feedback
5. **Monitor the automation** script to see when new emails arrive

---

## ❓ Troubleshooting

**Emails not showing up?**
- Check if `automation.py` is running
- Verify `pending_approvals.json` has data
- Refresh the browser

**Approve button not working?**
- Check browser console for errors
- Verify `approval_server.py` is running
- Check network tab in dev tools

**Emails not sending?**
- Verify `.env` configuration
- Check Gmail app password
- Review server logs

---

## 📞 Support

For issues or questions:
1. Check the logs in terminal
2. Review `pending_approvals.json`
3. Check browser console (F12)

---

**Enjoy your automated email approval system! 🎉**
