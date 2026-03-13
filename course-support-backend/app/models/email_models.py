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
    insight_tags: list[str]
    suggested_reply: str
    source_provider: str | None = None
    source_message_id: str | None = None
    webhook_event_id: str | None = None
    raw_payload_ref: str | None = None
    source_s3_key: str | None = None
    ses_message_id: str | None = None
    recipients: list[str] = Field(default_factory=list)
    attachment_names: list[str] = Field(default_factory=list)
    assigned_to: str | None = None
    thread_id: str | None = None


class EmailCreate(BaseModel):
    email_id: str | None = None
    course_id: str
    sender: str
    subject: str
    body: str
    received_at: str | None = None
    status: str = "pending_ai"
    classification: str = "unclassified"
    sentiment: str = "unknown"
    needs_escalation: bool = False
    insight_tags: list[str] = Field(default_factory=list)
    suggested_reply: str = ""
    source_provider: str | None = None
    source_message_id: str | None = None
    webhook_event_id: str | None = None
    raw_payload_ref: str | None = None
    source_s3_key: str | None = None
    ses_message_id: str | None = None
    recipients: list[str] = Field(default_factory=list)
    attachment_names: list[str] = Field(default_factory=list)
    assigned_to: str | None = None
    thread_id: str | None = None


class EmailListResponse(BaseModel):
    emails: list[Email]


class GenerateReplyResponse(BaseModel):
    message: str
    email: Email


class CreateEmailResponse(BaseModel):
    message: str
    email: Email


class ClassifyEmailResponse(BaseModel):
    message: str
    email: Email
