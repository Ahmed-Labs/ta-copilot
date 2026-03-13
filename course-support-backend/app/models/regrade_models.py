from pydantic import BaseModel


class RegradeRequestCreate(BaseModel):
    email_id: str
    student_email: str
    course_id: str
    assignment_name: str
    reason: str


class RegradeRequest(BaseModel):
    request_id: str
    email_id: str
    student_email: str
    course_id: str
    assignment_name: str
    reason: str
    status: str


class RegradeRequestListResponse(BaseModel):
    regrade_requests: list[RegradeRequest]


class CreateRegradeResponse(BaseModel):
    message: str
    request: RegradeRequest
