# Course Support Backend

FastAPI backend for the hackathon MVP that:

- lists incoming course emails
- generates placeholder AI replies for instructor review
- accepts regrade requests
- returns simple dashboard insights
- supports DynamoDB-backed storage for emails and regrade requests

## Current Scope

This backend supports two modes:

- local in-memory mode for development
- DynamoDB-backed mode for AWS integration

It is structured so you can later swap the placeholder AI and ingestion services for:

- Outlook or email-provider webhook + Lambda for ingestion
- Amazon Bedrock for reply generation
- DynamoDB for persistent storage
- ECS or EC2 for deployment

## Project Structure

```text
app/
  main.py
  config.py
  routes/
  services/
  models/
```

## Run Locally

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open:

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/health`

## Main Endpoints

- `GET /health`
- `GET /canvas/tools`
- `POST /canvas/call`
- `GET /emails`
- `POST /emails`
- `GET /emails/{email_id}`
- `POST /emails/{email_id}/classify`
- `POST /emails/{email_id}/generate-reply`
- `GET /insights/summary`
- `GET /regrade`
- `POST /regrade`

## Lambda Ingestion Payload

`POST /emails` is the API entry point for webhook/Lambda once the webhook payload has been parsed into a normalized email record.

Example payload:

```json
{
  "course_id": "ECE101",
  "sender": "student3@university.com",
  "subject": "Need help with rubric",
  "body": "I do not understand the grading rubric for question 2.",
  "source_provider": "outlook-webhook",
  "source_message_id": "msg-123",
  "webhook_event_id": "evt-123",
  "raw_payload_ref": "s3://hackathon-email-events/outlook/evt-123.json",
  "recipients": ["course101@yourdomain.com"],
  "attachment_names": ["screenshot.png"]
}
```

Compatibility note:

- `source_s3_key` and `ses_message_id` are still accepted for older test data, but they are no longer the primary ingestion fields.

## Canvas MCP

The backend can call Canvas MCP and inject the returned data into the AI prompt.

Set these environment variables:

- `USE_CANVAS_MCP=true`
- `CANVAS_MCP_URL=https://mcp.illinihunt.org/mcp`
- `CANVAS_API_URL=https://your-school.instructure.com/api/v1`
- `CANVAS_API_TOKEN=your_canvas_token`

For local Canvas MCP, run:

```powershell
.\scripts\start_local_canvas_mcp.ps1
```

and set:

```env
CANVAS_MCP_URL=http://127.0.0.1:8819/mcp
```

Important:

- `CANVAS_API_URL` must be your real institution Canvas API domain.
- `https://canvas.instructure.com/api/v1` returned `404 domain not found` during testing here, so it is not the correct API base for your account.

Use:

- `GET /canvas/tools` to inspect available Canvas tools
- `POST /canvas/call` to manually test a tool

You can also pass Canvas context into `POST /emails/{email_id}/classify` or `POST /emails/{email_id}/generate-reply` with:

```json
{
  "canvas_tool_name": "get_user_grades",
  "canvas_tool_arguments": {
    "courseIdentifier": "60365",
    "studentIdentifier": "student@example.edu"
  }
}
```

## Environment Variables

- `APP_NAME` default: `Course Support Backend`
- `AWS_REGION` default: `us-east-1`
- `CORS_ORIGINS` default: `*`
- `USE_DYNAMODB` default: `false`
- `USE_BEDROCK` default: `true`
- `BEDROCK_MODEL_ID` default: `us.amazon.nova-2-lite-v1:0`
- `USE_CANVAS_MCP` default: `false`
- `CANVAS_MCP_URL` default: `https://mcp.illinihunt.org/mcp`
- `CANVAS_API_URL` required for Canvas MCP
- `CANVAS_API_TOKEN` required for Canvas MCP
- `EMAILS_TABLE` default: `Emails`
- `REGRADE_REQUESTS_TABLE` default: `RegradeRequests`

## DynamoDB Setup

1. Configure AWS credentials in your shell or AWS profile.
2. Copy `.env.example` to `.env`.
3. Set `USE_DYNAMODB=true` in `.env`.
4. Run the bootstrap script:

```powershell
venv\Scripts\Activate.ps1
python scripts\bootstrap_dynamodb.py
```

This creates two on-demand tables:

- `Emails` with partition key `email_id`
- `RegradeRequests` with partition key `request_id`

The script also seeds two sample email records so `/emails` works immediately.

When `USE_DYNAMODB=false`, the app keeps using local fake data.

## Docker

Build and run:

```powershell
docker build -t course-support-backend .
docker run -p 8000:8000 course-support-backend
```

This Dockerfile is suitable as a starting point for ECS.
