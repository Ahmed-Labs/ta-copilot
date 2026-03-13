# ✅ FIXED: DynamoDB Setup Steps

## 🔍 What I Found:
- ✅ EC2 has IAM role: `vscodeserver-CodeServerIAMRole-rVfvxo0mdmJf`
- ❌ Role doesn't have DynamoDB permissions
- ❌ Credentials file has expired session tokens

## 🔧 Your Teammate Needs To (AWS Console):

### Step 1: Add DynamoDB Permissions to IAM Role

1. **Go to:** AWS Console → IAM → Roles
2. **Search for:** `vscodeserver-CodeServerIAMRole-rVfvxo0mdmJf`
3. **Click the role**
4. **Click "Add permissions" → "Attach policies"**
5. **Search and select:** `AmazonDynamoDBFullAccess`
6. **Click "Add permissions"**

**That's it!** No need to restart EC2.

---

## 🚀 Then I'll Run (Automatically):

Once permissions are added, run these commands:

```bash
# Remove expired credentials to use instance role
mv ~/.aws/credentials ~/.aws/credentials.old

# Create DynamoDB tables
cd /home/ec2-user/ta-copilot/course-support-backend
source venv/bin/activate
python scripts/bootstrap_dynamodb.py

# Enable DynamoDB in backend
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

# Wait and test
sleep 3
curl http://localhost:8000/health
```

---

## ✅ Verify It Works:

```bash
# Check tables created
aws dynamodb list-tables --region us-west-2

# Should show:
# {
#     "TableNames": [
#         "Emails",
#         "RegradeRequests"
#     ]
# }

# Test backend with DynamoDB
curl http://18.236.97.111:8000/emails
```

---

## 📊 What This Does:

**Creates 2 DynamoDB Tables:**
1. `Emails` - Stores all student emails
2. `RegradeRequests` - Stores regrade requests

**Seeds Sample Data:**
- 2 sample emails automatically added

**Enables Persistence:**
- Emails survive backend restarts
- Data stored permanently in DynamoDB

---

## 🎯 Quick Summary:

**Your teammate:** Add `AmazonDynamoDBFullAccess` to IAM role `vscodeserver-CodeServerIAMRole-rVfvxo0mdmJf`

**Then tell me:** "Permissions added"

**I'll run:** All the setup commands above

**Result:** ✅ Persistent storage with DynamoDB!

---

**IAM Role Name:** `vscodeserver-CodeServerIAMRole-rVfvxo0mdmJf`
**Policy Needed:** `AmazonDynamoDBFullAccess`
**Time:** 2 minutes
