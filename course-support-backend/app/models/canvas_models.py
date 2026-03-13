from __future__ import annotations

from pydantic import BaseModel, Field


class CanvasToolInfo(BaseModel):
    name: str
    description: str | None = None
    input_schema: dict | None = None


class CanvasToolListResponse(BaseModel):
    tools: list[CanvasToolInfo]


class CanvasToolCallRequest(BaseModel):
    tool_name: str
    arguments: dict = Field(default_factory=dict)


class CanvasToolCallResponse(BaseModel):
    tool_name: str
    raw_result: dict
    text_content: list[str] = Field(default_factory=list)
    structured_content: dict | None = None
    is_error: bool = False


class AgentCanvasContextRequest(BaseModel):
    canvas_tool_name: str | None = None
    canvas_tool_arguments: dict = Field(default_factory=dict)
    include_course_context: bool = True
    course_identifier: str | None = None
