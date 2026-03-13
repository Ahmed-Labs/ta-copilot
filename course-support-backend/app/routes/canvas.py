from fastapi import APIRouter, HTTPException

from app.models.canvas_models import (
    CanvasToolCallRequest,
    CanvasToolCallResponse,
    CanvasToolInfo,
    CanvasToolListResponse,
)
from app.services.canvas_mcp_service import (
    CanvasMcpError,
    call_canvas_tool,
    list_canvas_tools,
)
from app.services.course_context_service import fetch_canvas_course_context

router = APIRouter()


@router.get("/tools", response_model=CanvasToolListResponse)
def get_canvas_tools():
    try:
        tools = list_canvas_tools()
    except CanvasMcpError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "tools": [
            CanvasToolInfo(
                name=tool.get("name", ""),
                description=tool.get("description"),
                input_schema=tool.get("inputSchema"),
            )
            for tool in tools
        ]
    }


@router.post("/call", response_model=CanvasToolCallResponse)
def call_canvas_tool_endpoint(payload: CanvasToolCallRequest):
    try:
        result = call_canvas_tool(
            tool_name=payload.tool_name,
            arguments=payload.arguments,
        )
    except CanvasMcpError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    text_content = [
        item["text"]
        for item in result.get("content", [])
        if item.get("type") == "text" and item.get("text")
    ]
    return {
        "tool_name": payload.tool_name,
        "raw_result": result,
        "text_content": text_content,
        "structured_content": result.get("structuredContent"),
        "is_error": bool(result.get("isError")),
    }


@router.get("/course-context/{course_identifier}")
def get_course_context(course_identifier: str):
    try:
        context = fetch_canvas_course_context(course_identifier)
    except CanvasMcpError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "course_identifier": course_identifier,
        "context": context,
    }
