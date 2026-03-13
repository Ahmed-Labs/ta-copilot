from __future__ import annotations
from typing import Optional, List

from pydantic import BaseModel, Field


class CanvasToolInfo(BaseModel):
    name: str
    description: Optional[str] = None
    input_schema: Optional[dict] = None


class CanvasToolListResponse(BaseModel):
    tools: List[CanvasToolInfo]


class CanvasToolCallRequest(BaseModel):
    tool_name: str
    arguments: dict = Field(default_factory=dict)


class CanvasToolCallResponse(BaseModel):
    tool_name: str
    raw_result: dict
    text_content: List[str] = Field(default_factory=list)
    structured_content: Optional[dict] = None
    is_error: bool = False


class AgentCanvasContextRequest(BaseModel):
    canvas_tool_name: Optional[str] = None
    canvas_tool_arguments: dict = Field(default_factory=dict)
    include_course_context: bool = True
    course_identifier: Optional[str] = None
