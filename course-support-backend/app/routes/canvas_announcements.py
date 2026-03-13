from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests
from app.config import settings
from app.services.dynamodb_service import get_email_by_id, update_email_reply

router = APIRouter()


class SendAnnouncementRequest(BaseModel):
    course_id: str
    title: str
    message: str


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
