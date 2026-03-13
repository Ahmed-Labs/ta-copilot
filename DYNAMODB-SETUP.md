# 🔧 DynamoDB Setup Guide

## ❌ Current Issue:
AWS credentials on EC2 are **expired/invalid**

## ✅ Solution - Your Teammate Needs To:

### Option 1: Attach IAM Role to EC2 (Recommended)

1. **Go to AWS Console → IAM → Roles**
2. **Create new role:**
   - Trusted entity: AWS service → EC2
   - Permissions: `AmazonDynamoDBFullAccess`
   - Name: `EC2-DynamoDB-Role`

3. **Attach to EC2:**
   - Go to EC2 → Instances
   - Select your instance
   - Actions → Security → Modify IAM role
   - Select `EC2-DynamoDB-Role`
   - Save

4. **No restart needed!** EC2 will automatically use the role

### Option 2: Update AWS Credentials

```bash
aws configure
# Enter valid AWS Access Key ID
# Enter valid AWS Secret Access Key
# Region: us-west-2
```

---

## 📊 Then Run Bootstrap Script:

```bash
cd /home/ec2-user/ta-copilot/course-support-backend
source venv/bin/activate
python scripts/bootstrap_dynamodb.py
```

This creates:
- ✅ `Emails` table
- ✅ `RegradeRequests` table
- ✅ Seeds 2 sample emails

---

## 🔄 Enable DynamoDB in Backend:

```bash
cd /home/ec2-user/ta-copilot/course-support-backend

# Update .env
cat > .env << 'EOF'
USE_DYNAMODB=true
USE_BEDROCK=false
USE_CANVAS_MCP=false
CORS_ORIGINS=*
AWS_REGION=us-west-2
EOF

# Restart backend
pkill -f uvicorn
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
```

---

## ✅ Verify It Works:

```bash
# Check tables exist
aws dynamodb list-tables --region us-west-2

# Test backend
curl http://18.236.97.111:8000/emails
```

---

## 🎯 What This Fixes:

**Before (In-Memory):**
```
Email → Backend (RAM) → Lost on restart ❌
```

**After (DynamoDB):**
```
Email → Backend → DynamoDB → Persistent ✅
```

---

**Ask your teammate to attach IAM role or update credentials, then I'll help run the setup!**
