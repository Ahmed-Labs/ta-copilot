from typing import Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import requests
from app.config import settings
from app.services.dynamodb_service import get_email_by_id, update_email_reply, create_email
from app.models.email_models import EmailCreate

router = APIRouter()


class SendAnnouncementRequest(BaseModel):
    course_id: str
    title: str
    message: str


class LambdaEmailWebhook(BaseModel):
    """Webhook payload from Lambda when new email arrives"""
    sender: str
    subject: str
    body: str
    course_id: Optional[str] = None
    message_id: Optional[str] = None
    recipients: Optional[list] = None
    received_at: Optional[str] = None


@router.post("/webhook/email")
async def receive_email_from_lambda(payload: LambdaEmailWebhook):
    """
    Webhook endpoint for Lambda to send new emails.
    Lambda URL: http://18.236.97.111:8000/announcements/webhook/email
    """
    
    # Create email in database
    email_data = EmailCreate(
        course_id=payload.course_id or "INBOX",
        sender=payload.sender,
        subject=payload.subject,
        body=payload.body,
        source_provider="lambda-webhook",
        source_message_id=payload.message_id,
        recipients=payload.recipients or [],
        received_at=payload.received_at
    )
    
    email = create_email(email_data)
    
    if not email:
        raise HTTPException(status_code=409, detail="Email already exists or failed to create")
    
    return {
        "success": True,
        "message": "Email received and stored",
        "email_id": email.email_id
    }


@router.post("/send-announcement")
async def send_announcement(payload: SendAnnouncementRequest):
    """Send announcement to Canvas course"""
    
    if not settings.use_canvas_mcp:
        raise HTTPException(status_code=400, detail="Canvas MCP not enabled")
    
    if not settings.canvas_api_token or settings.canvas_api_token == "YOUR_TOKEN_HERE":
        raise HTTPException(status_code=400, detail="Canvas API token not configured")
    
    # Post announcement to Canvas
    url = f"{settings.canvas_api_url}/courses/{payload.course_id}/discussion_topics"
    headers = {
        "Authorization": f"Bearer {settings.canvas_api_token}",
        "Content-Type": "application/json"
    }
    data = {
        "title": payload.title,
        "message": payload.message,
        "is_announcement": True,
        "published": True
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        response.raise_for_status()
        return {
            "success": True,
            "message": "Announcement posted to Canvas",
            "canvas_response": response.json()
        }
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to post to Canvas: {str(e)}")


@router.post("/emails/{email_id}/send-reply")
async def send_email_reply(email_id: str, course_id: Optional[str] = None):
    """Send email reply as Canvas announcement"""
    
    email = get_email_by_id(email_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    if not email.suggested_reply:
        raise HTTPException(status_code=400, detail="No reply to send. Generate a reply first.")
    
    # Use course_id from request or email
    target_course = course_id or email.course_id
    
    # Create announcement
    announcement = SendAnnouncementRequest(
        course_id=target_course,
        title=f"Re: {email.subject}",
        message=email.suggested_reply
    )
    
    result = await send_announcement(announcement)
    
    # Update email status
    update_email_reply(
        email_id=email_id,
        suggested_reply=email.suggested_reply,
        status="sent"
    )
    
    return {
        "success": True,
        "message": "Reply sent as Canvas announcement",
        "email_id": email_id,
        "canvas_response": result
    }
