from fastapi import APIRouter, HTTPException
from app.models.canvas_models import AgentCanvasContextRequest
from app.models.email_models import (
    ClassifyEmailResponse,
    CreateEmailResponse,
    Email,
    EmailCreate,
    EmailListResponse,
    GenerateReplyResponse,
)
from app.services.dynamodb_service import (
    create_email,
    get_all_emails,
    get_email_by_id,
    update_email_reply,
)
from app.services.bedrock_service import analyze_email
from app.services.canvas_mcp_service import (
    CanvasMcpError,
    call_canvas_tool,
    summarize_canvas_tool_result,
)
from app.services.course_context_service import fetch_canvas_course_context

router = APIRouter()


@router.get("", response_model=EmailListResponse)
def list_emails():
    return {"emails": get_all_emails()}


@router.post("", response_model=CreateEmailResponse, status_code=201)
def create_email_record(payload: EmailCreate):
    email = create_email(payload)
    if not email:
        raise HTTPException(status_code=409, detail="Email already exists")
    return {
        "message": "Email created successfully",
        "email": email,
    }


@router.get("/{email_id}", response_model=Email)
def get_email(email_id: str):
    email = get_email_by_id(email_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    return email


@router.post("/{email_id}/classify", response_model=ClassifyEmailResponse)
def classify_email(email_id: str, payload: AgentCanvasContextRequest | None = None):
    email = get_email_by_id(email_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    additional_context = _get_canvas_context(email, payload)
    ai_result = analyze_email(
        subject=email.subject,
        body=email.body,
        current_classification=email.classification,
        additional_context=additional_context,
    )
    updated_email = update_email_reply(
        email_id=email_id,
        suggested_reply=email.suggested_reply,
        status="classified",
        classification=ai_result["classification"],
        needs_escalation=ai_result["needs_escalation"],
        insight_tags=ai_result["insight_tags"],
        sentiment=ai_result["sentiment"],
        assigned_to=ai_result["assigned_to"],
    )
    if not updated_email:
        raise HTTPException(status_code=500, detail="Failed to classify email")

    return {
        "message": "Email classified successfully",
        "email": updated_email,
    }


@router.post("/{email_id}/generate-reply", response_model=GenerateReplyResponse)
def generate_reply(email_id: str, payload: AgentCanvasContextRequest | None = None):
    email = get_email_by_id(email_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    additional_context = _get_canvas_context(email, payload)
    ai_result = analyze_email(
        subject=email.subject,
        body=email.body,
        current_classification=email.classification,
        additional_context=additional_context,
    )
    updated_email = update_email_reply(
        email_id=email_id,
        suggested_reply=ai_result["suggested_reply"],
        status="review_ready",
        classification=ai_result["classification"],
        needs_escalation=ai_result["needs_escalation"],
        insight_tags=ai_result["insight_tags"],
        sentiment=ai_result["sentiment"],
        assigned_to=ai_result["assigned_to"],
    )
    if not updated_email:
        raise HTTPException(status_code=500, detail="Failed to update email")

    return {
        "message": "Suggested reply generated successfully",
        "email": updated_email,
    }


def _get_canvas_context(
    email: Email,
    payload: AgentCanvasContextRequest | None,
) -> str | None:
    context_sections: list[str] = []
    request_payload = payload or AgentCanvasContextRequest()

    course_identifier = request_payload.course_identifier or email.course_id
    if request_payload.include_course_context and course_identifier:
        try:
            course_context = fetch_canvas_course_context(course_identifier)
        except CanvasMcpError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        if course_context:
            context_sections.append(
                f"Latest Canvas course context for {course_identifier}:\n{course_context}"
            )

    if request_payload.canvas_tool_name:
        try:
            result = call_canvas_tool(
                tool_name=request_payload.canvas_tool_name,
                arguments=request_payload.canvas_tool_arguments,
            )
        except CanvasMcpError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        if result.get("isError"):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Canvas MCP tool returned an error for "
                    f"{request_payload.canvas_tool_name}."
                ),
            )

        tool_summary = summarize_canvas_tool_result(result)
        if tool_summary:
            context_sections.append(
                f"Additional Canvas tool output from "
                f"{request_payload.canvas_tool_name}:\n{tool_summary}"
            )

    return "\n\n".join(section for section in context_sections if section).strip() or None
