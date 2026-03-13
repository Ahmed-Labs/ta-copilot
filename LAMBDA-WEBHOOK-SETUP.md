# 🎯 Lambda → Backend Integration Complete!

## ✅ **Webhook Endpoint Created:**

**URL:** `http://18.236.97.111:8000/announcements/webhook/email`

**Method:** POST

**What it does:**
- Receives emails from Lambda
- Stores in DynamoDB
- Shows up in dashboard automatically

---

## 📨 **Lambda Payload Format:**

Your Lambda should send this JSON:

```json
{
  "sender": "student@university.edu",
  "subject": "Question about assignment",
  "body": "Email body text here...",
  "course_id": "ECE101",
  "message_id": "unique-message-id",
  "recipients": ["instructor@university.edu"],
  "received_at": "2026-03-13T18:00:00Z"
}
```

**Required fields:**
- `sender` - Student email address
- `subject` - Email subject
- `body` - Email content

**Optional fields:**
- `course_id` - Course identifier (defaults to "INBOX")
- `message_id` - Unique message ID from Outlook
- `recipients` - List of recipients
- `received_at` - Timestamp (auto-generated if not provided)

---

## 🔧 **Lambda Configuration:**

Update your Lambda function to call:

```python
import requests
import json

def lambda_handler(event, context):
    # Parse email from Microsoft Graph webhook
    email_data = {
        "sender": event['from']['emailAddress']['address'],
        "subject": event['subject'],
        "body": event['body']['content'],
        "course_id": "ECE101",  # Extract from email or subject
        "message_id": event['id'],
        "recipients": [r['emailAddress']['address'] for r in event.get('toRecipients', [])],
        "received_at": event.get('receivedDateTime')
    }
    
    # Send to backend
    response = requests.post(
        'http://18.236.97.111:8000/announcements/webhook/email',
        json=email_data,
        timeout=10
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Email forwarded to backend'})
    }
```

---

## 🧪 **Test Results:**

**Test email sent:**
```
Subject: Question about final exam
From: student@university.edu
Body: Hi Professor, when is the final exam scheduled?
```

**Result:**
- ✅ Received by webhook
- ✅ Stored in DynamoDB
- ✅ Email ID: cb675ecf-fca5-49cc-adb9-fb7d17e1bac9
- ✅ Total emails now: 11
- ✅ Shows up in dashboard

---

## 🔄 **Complete Flow:**

```
Student sends email in Outlook
    ↓
Microsoft Graph detects new email
    ↓
Calls Lambda webhook
    ↓
Lambda parses email
    ↓
Lambda POSTs to: http://18.236.97.111:8000/announcements/webhook/email
    ↓
Backend stores in DynamoDB
    ↓
Dashboard auto-refreshes (30 seconds)
    ↓
Instructor sees new email!
```

---

## 📊 **What Happens in Dashboard:**

1. **Email appears in list** (within 30 seconds)
2. **Shows:** Subject, sender, course
3. **Instructor can:**
   - Click to view
   - Classify with AI
   - Generate reply
   - Send to Canvas

---

## 🎯 **Lambda Environment Variables:**

Add to your Lambda:
```
BACKEND_URL=http://18.236.97.111:8000
WEBHOOK_ENDPOINT=/announcements/webhook/email
```

Then in code:
```python
import os
backend_url = os.environ['BACKEND_URL']
endpoint = os.environ['WEBHOOK_ENDPOINT']
url = f"{backend_url}{endpoint}"
```

---

## ✅ **Testing the Webhook:**

**From command line:**
```bash
curl -X POST http://18.236.97.111:8000/announcements/webhook/email \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "test@student.edu",
    "subject": "Test Email",
    "body": "This is a test",
    "course_id": "TEST101"
  }'
```

**Expected response:**
```json
{
  "success": true,
  "message": "Email received and stored",
  "email_id": "uuid-here"
}
```

---

## 🔒 **Security (Optional):**

Add authentication to webhook:

**1. Add API key to Lambda:**
```python
headers = {
    'Content-Type': 'application/json',
    'X-API-Key': 'your-secret-key'
}
```

**2. Validate in backend:**
```python
@router.post("/webhook/email")
async def receive_email_from_lambda(payload: LambdaEmailWebhook, request: Request):
    api_key = request.headers.get('X-API-Key')
    if api_key != 'your-secret-key':
        raise HTTPException(status_code=401, detail="Unauthorized")
    # ... rest of code
```

---

## 🎊 **Summary:**

**Endpoint:** ✅ Created and working
**URL:** http://18.236.97.111:8000/announcements/webhook/email
**Tested:** ✅ Email received and stored
**Dashboard:** ✅ Shows new emails automatically
**Lambda:** Ready to integrate

**Your Lambda just needs to POST to this endpoint!** 🚀
