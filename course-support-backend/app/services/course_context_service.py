from __future__ import annotations
from typing import Optional, List

from app.services.canvas_mcp_service import (
    CanvasMcpError,
    call_canvas_tool,
    summarize_canvas_tool_result,
)


def fetch_canvas_course_context(course_identifier: str) -> str:
    sections: List[str] = []

    tool_calls = [
        ("get_course_details", {"course_identifier": course_identifier}),
        ("list_announcements", {"course_identifier": course_identifier}),
        ("list_assignments", {"course_identifier": course_identifier}),
    ]

    for tool_name, arguments in tool_calls:
        try:
            result = call_canvas_tool(tool_name=tool_name, arguments=arguments)
        except CanvasMcpError as exc:
            sections.append(f"{tool_name} error: {exc}")
            continue

        if result.get("isError"):
            sections.append(f"{tool_name} error: {result}")
            continue

        summary = summarize_canvas_tool_result(result).strip()
        if summary:
            sections.append(summary)

    return "\n\n".join(sections).strip()
