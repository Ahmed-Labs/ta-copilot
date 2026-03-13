# 🚀 Quick Start Guide

## For Instructors (2 minutes)

### **Step 1: Download Dashboard**
1. Go to: https://github.com/Ahmed-Labs/ta-copilot
2. Download `instructor-dashboard.html`
3. Open in Chrome/Firefox

### **Step 2: Use Dashboard**
- See all student emails
- Click email → View details
- Click "Classify" → AI categorizes
- Click "Generate Reply" → AI suggests response
- Click "Send to Canvas" → Posts announcement

**That's it!** ✅

---

## For Developers (5 minutes)

### **Backend is Running:**
```
http://18.236.97.111:8000
```

### **Lambda Integration:**
POST emails to:
```
http://18.236.97.111:8000/announcements/webhook/email
```

Payload:
```json
{
  "sender": "student@email.com",
  "subject": "Question",
  "body": "Email content"
}
```

### **Test It:**
```bash
curl http://18.236.97.111:8000/health
curl http://18.236.97.111:8000/emails
```

**Done!** ✅

---

## Key URLs

- **Backend:** http://18.236.97.111:8000
- **API Docs:** http://18.236.97.111:8000/docs
- **Canvas Course:** https://canvas.instructure.com/courses/14388425
- **GitHub:** https://github.com/Ahmed-Labs/ta-copilot

---

## Demo in 2 Minutes

1. **Show dashboard** → 11 emails
2. **Click email** → View details
3. **Click "Classify"** → AI categorizes
4. **Click "Generate Reply"** → AI suggests
5. **Click "Send to Canvas"** → Posted!
6. **Open Canvas** → Show announcement

**Value:** Saves 5-10 hours/week for instructors! 🎉
