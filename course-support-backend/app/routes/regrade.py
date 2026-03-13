from fastapi import APIRouter
from app.models.regrade_models import (
    CreateRegradeResponse,
    RegradeRequestCreate,
    RegradeRequestListResponse,
)
from app.services.dynamodb_service import (
    create_regrade_request as create_regrade_request_record,
    get_all_regrade_requests,
)

router = APIRouter()


@router.get("", response_model=RegradeRequestListResponse)
def get_regrade_requests():
    return {"regrade_requests": get_all_regrade_requests()}


@router.post("", response_model=CreateRegradeResponse)
def create_regrade_request(payload: RegradeRequestCreate):
    new_request = create_regrade_request_record(
        email_id=payload.email_id,
        student_email=payload.student_email,
        course_id=payload.course_id,
        assignment_name=payload.assignment_name,
        reason=payload.reason,
    )
    return {
        "message": "Regrade request created successfully",
        "request": new_request,
    }
