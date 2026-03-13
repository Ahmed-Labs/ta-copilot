from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.config import settings
from app.models.email_models import Email, EmailCreate
from app.models.regrade_models import RegradeRequest

fake_emails = [
    Email(
        email_id="1",
        course_id="ECE101",
        sender="student1@university.com",
        subject="Question about assignment deadline",
        body="Hi professor, is the assignment due tonight at 11:59 PM?",
        received_at="2026-03-13T10:00:00Z",
        status="pending_review",
        classification="routine",
        sentiment="neutral",
        needs_escalation=False,
        insight_tags=["assignment", "deadline"],
        suggested_reply="Hi, yes, the assignment is due tonight at 11:59 PM as stated on the course page.",
        source_provider="seed",
        source_message_id="seed-1",
        ),
    Email(
        email_id="2",
        course_id="ECE101",
        sender="student2@university.com",
        subject="Regrade request for quiz 2",
        body="Hello, I think my short answer for question 3 deserves more marks.",
        received_at="2026-03-13T11:00:00Z",
        status="flagged",
        classification="regrade",
        sentiment="frustrated",
        needs_escalation=True,
        insight_tags=["regrade", "quiz2"],
        suggested_reply="Thanks for reaching out. Your request has been noted and will be reviewed according to the course regrade policy.",
        source_provider="seed",
        source_message_id="seed-2",
    ),
]

fake_regrade_requests: list[RegradeRequest] = []


def get_all_emails():
    if settings.use_dynamodb:
        emails = _scan_emails_from_dynamodb()
        return sorted(emails, key=lambda item: item.received_at, reverse=True)
    return fake_emails


def get_email_by_id(email_id: str):
    if settings.use_dynamodb:
        return _get_email_from_dynamodb(email_id)
    for email in fake_emails:
        if email.email_id == email_id:
            return email
    return None


def update_email_reply(
    email_id: str,
    suggested_reply: str,
    status: str,
    classification: str | None = None,
    needs_escalation: bool | None = None,
    insight_tags: list[str] | None = None,
    sentiment: str | None = None,
    assigned_to: str | None = None,
):
    if settings.use_dynamodb:
        return _update_email_in_dynamodb(
            email_id=email_id,
            suggested_reply=suggested_reply,
            status=status,
            classification=classification,
            needs_escalation=needs_escalation,
            insight_tags=insight_tags,
            sentiment=sentiment,
            assigned_to=assigned_to,
        )

    email = get_email_by_id(email_id)
    if not email:
        return None

    email.suggested_reply = suggested_reply
    email.status = status

    if classification is not None:
        email.classification = classification
    if needs_escalation is not None:
        email.needs_escalation = needs_escalation
    if insight_tags is not None:
        email.insight_tags = insight_tags
    if sentiment is not None:
        email.sentiment = sentiment
    if assigned_to is not None:
        email.assigned_to = assigned_to

    return email


def create_email(payload: EmailCreate):
    email = Email(
        email_id=payload.email_id or str(uuid4()),
        course_id=payload.course_id,
        sender=payload.sender,
        subject=payload.subject,
        body=payload.body,
        received_at=payload.received_at or datetime.now(timezone.utc).isoformat(),
        status=payload.status,
        classification=payload.classification,
        sentiment=payload.sentiment,
        needs_escalation=payload.needs_escalation,
        insight_tags=payload.insight_tags,
        suggested_reply=payload.suggested_reply,
        source_provider=payload.source_provider or "webhook",
        source_message_id=payload.source_message_id or payload.ses_message_id,
        webhook_event_id=payload.webhook_event_id,
        raw_payload_ref=payload.raw_payload_ref or payload.source_s3_key,
        source_s3_key=payload.source_s3_key,
        ses_message_id=payload.ses_message_id,
        recipients=payload.recipients,
        attachment_names=payload.attachment_names,
        assigned_to=payload.assigned_to,
        thread_id=payload.thread_id,
    )

    if settings.use_dynamodb:
        return _put_email_in_dynamodb(email)

    if get_email_by_id(email.email_id):
        return None

    fake_emails.insert(0, email)
    return email


def get_all_regrade_requests():
    if settings.use_dynamodb:
        return _scan_regrade_requests_from_dynamodb()
    return fake_regrade_requests


def create_regrade_request(
    email_id: str,
    student_email: str,
    course_id: str,
    assignment_name: str,
    reason: str,
):
    request = RegradeRequest(
        request_id=str(uuid4()),
        email_id=email_id,
        student_email=student_email,
        course_id=course_id,
        assignment_name=assignment_name,
        reason=reason,
        status="pending",
    )

    if settings.use_dynamodb:
        return _put_regrade_request_in_dynamodb(request)

    fake_regrade_requests.append(request)
    return request


def _get_dynamodb_resource():
    return boto3.resource("dynamodb", region_name=settings.aws_region)


def _emails_table():
    return _get_dynamodb_resource().Table(settings.emails_table)


def _regrade_requests_table():
    return _get_dynamodb_resource().Table(settings.regrade_requests_table)


def _scan_emails_from_dynamodb():
    try:
        items = _scan_all_items(_emails_table())
        return [Email.model_validate(item) for item in items]
    except (ClientError, BotoCoreError) as exc:
        raise RuntimeError(f"Failed to scan DynamoDB emails table: {exc}") from exc


def _get_email_from_dynamodb(email_id: str):
    try:
        response = _emails_table().get_item(Key={"email_id": email_id})
        item = response.get("Item")
        return Email.model_validate(item) if item else None
    except (ClientError, BotoCoreError) as exc:
        raise RuntimeError(f"Failed to read email from DynamoDB: {exc}") from exc


def _update_email_in_dynamodb(
    email_id: str,
    suggested_reply: str,
    status: str,
    classification: str | None = None,
    needs_escalation: bool | None = None,
    insight_tags: list[str] | None = None,
    sentiment: str | None = None,
    assigned_to: str | None = None,
):
    expression_names = {
        "#suggested_reply": "suggested_reply",
        "#status": "status",
    }
    expression_values = {
        ":suggested_reply": suggested_reply,
        ":status": status,
    }
    update_parts = [
        "#suggested_reply = :suggested_reply",
        "#status = :status",
    ]

    if classification is not None:
        expression_names["#classification"] = "classification"
        expression_values[":classification"] = classification
        update_parts.append("#classification = :classification")
    if needs_escalation is not None:
        expression_names["#needs_escalation"] = "needs_escalation"
        expression_values[":needs_escalation"] = needs_escalation
        update_parts.append("#needs_escalation = :needs_escalation")
    if insight_tags is not None:
        expression_names["#insight_tags"] = "insight_tags"
        expression_values[":insight_tags"] = insight_tags
        update_parts.append("#insight_tags = :insight_tags")
    if sentiment is not None:
        expression_names["#sentiment"] = "sentiment"
        expression_values[":sentiment"] = sentiment
        update_parts.append("#sentiment = :sentiment")
    if assigned_to is not None:
        expression_names["#assigned_to"] = "assigned_to"
        expression_values[":assigned_to"] = assigned_to
        update_parts.append("#assigned_to = :assigned_to")

    try:
        response = _emails_table().update_item(
            Key={"email_id": email_id},
            UpdateExpression="SET " + ", ".join(update_parts),
            ExpressionAttributeNames=expression_names,
            ExpressionAttributeValues=expression_values,
            ConditionExpression="attribute_exists(email_id)",
            ReturnValues="ALL_NEW",
        )
        return Email.model_validate(response["Attributes"])
    except _emails_table().meta.client.exceptions.ConditionalCheckFailedException:
        return None
    except (ClientError, BotoCoreError) as exc:
        raise RuntimeError(f"Failed to update email in DynamoDB: {exc}") from exc


def _put_email_in_dynamodb(email: Email):
    table = _emails_table()
    try:
        table.put_item(
            Item=email.model_dump(),
            ConditionExpression="attribute_not_exists(email_id)",
        )
        return email
    except table.meta.client.exceptions.ConditionalCheckFailedException:
        return None
    except (ClientError, BotoCoreError) as exc:
        raise RuntimeError(f"Failed to save email in DynamoDB: {exc}") from exc


def _scan_regrade_requests_from_dynamodb():
    try:
        items = _scan_all_items(_regrade_requests_table())
        return [RegradeRequest.model_validate(item) for item in items]
    except (ClientError, BotoCoreError) as exc:
        raise RuntimeError(
            f"Failed to scan DynamoDB regrade requests table: {exc}"
        ) from exc


def _put_regrade_request_in_dynamodb(request: RegradeRequest):
    try:
        _regrade_requests_table().put_item(Item=request.model_dump())
        return request
    except (ClientError, BotoCoreError) as exc:
        raise RuntimeError(
            f"Failed to save regrade request in DynamoDB: {exc}"
        ) from exc


def _scan_all_items(table):
    response = table.scan()
    items = response.get("Items", [])

    while "LastEvaluatedKey" in response:
        response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
        items.extend(response.get("Items", []))

    return items
