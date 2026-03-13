from typing import Optional, List
from pydantic import BaseModel, Field


class Email(BaseModel):
    email_id: str
    course_id: str
    sender: str
    subject: str
    body: str
    received_at: str
    status: str
    classification: str
    sentiment: str
    needs_escalation: bool
    insight_tags: List[str]
    suggested_reply: str
    source_provider: Optional[str] = None
    source_message_id: Optional[str] = None
    webhook_event_id: Optional[str] = None
    raw_payload_ref: Optional[str] = None
    source_s3_key: Optional[str] = None
    ses_message_id: Optional[str] = None
    recipients: List[str] = Field(default_factory=list)
    attachment_names: List[str] = Field(default_factory=list)
    assigned_to: Optional[str] = None
    thread_id: Optional[str] = None


class EmailCreate(BaseModel):
    email_id: Optional[str] = None
    course_id: str
    sender: str
    subject: str
    body: str
    received_at: Optional[str] = None
    status: str = "pending_ai"
    classification: str = "unclassified"
    sentiment: str = "unknown"
    needs_escalation: bool = False
    insight_tags: List[str] = Field(default_factory=list)
    suggested_reply: str = ""
    source_provider: Optional[str] = None
    source_message_id: Optional[str] = None
    webhook_event_id: Optional[str] = None
    raw_payload_ref: Optional[str] = None
    source_s3_key: Optional[str] = None
    ses_message_id: Optional[str] = None
    recipients: List[str] = Field(default_factory=list)
    attachment_names: List[str] = Field(default_factory=list)
    assigned_to: Optional[str] = None
    thread_id: Optional[str] = None


class EmailListResponse(BaseModel):
    emails: List[Email]


class GenerateReplyResponse(BaseModel):
    message: str
    email: Email


class CreateEmailResponse(BaseModel):
    message: str
    email: Email


class ClassifyEmailResponse(BaseModel):
    message: str
    email: Email
