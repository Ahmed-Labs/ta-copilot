from __future__ import annotations
from typing import Optional, List

import json
from itertools import count
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.config import settings


class CanvasMcpError(RuntimeError):
    pass


class CanvasMcpClient:
    def __init__(self) -> None:
        self._session_id: Optional[str] = None
        self._protocol_version = "2025-03-26"
        self._request_ids = count(1)

    def list_tools(self) -> List[dict]:
        self._initialize_if_needed()
        response = self._post_json(
            payload={
                "jsonrpc": "2.0",
                "id": next(self._request_ids),
                "method": "tools/list",
                "params": {},
            }
        )
        return response.get("result", {}).get("tools", [])

    def call_tool(self, tool_name: str, arguments: Optional[dict] = None) -> dict:
        self._initialize_if_needed()
        response = self._post_json(
            payload={
                "jsonrpc": "2.0",
                "id": next(self._request_ids),
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments or {},
                },
            }
        )
        return response.get("result", {})

    def _initialize_if_needed(self) -> None:
        if self._session_id is not None:
            return

        response, headers = self._post_json(
            payload={
                "jsonrpc": "2.0",
                "id": next(self._request_ids),
                "method": "initialize",
                "params": {
                    "protocolVersion": self._protocol_version,
                    "capabilities": {"tools": {}},
                    "clientInfo": {
                        "name": "course-support-backend",
                        "version": "0.1.0",
                    },
                },
            },
            include_headers=True,
        )
        result = response.get("result")
        if not result:
            raise CanvasMcpError("Canvas MCP initialize returned no result.")

        self._protocol_version = result.get("protocolVersion", self._protocol_version)
        lowered_headers = {key.lower(): value for key, value in headers.items()}
        self._session_id = lowered_headers.get("mcp-session-id")
        self._post_notification(
            {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
            }
        )

    def _post_notification(self, payload: dict) -> None:
        try:
            self._post_json(payload=payload)
        except CanvasMcpError:
            pass

    def _post_json(self, payload: dict, include_headers: bool = False):
        headers = {
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
            "MCP-Protocol-Version": self._protocol_version,
        }
        if self._session_id:
            headers["MCP-Session-Id"] = self._session_id
        if settings.canvas_api_token:
            headers["X-Canvas-Token"] = settings.canvas_api_token
        if settings.canvas_api_url:
            headers["X-Canvas-URL"] = settings.canvas_api_url

        request = Request(
            settings.canvas_mcp_url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urlopen(request, timeout=30) as response:
                raw_body = response.read().decode("utf-8").strip()
                parsed = _decode_mcp_response_body(raw_body) if raw_body else {}
                if "error" in parsed:
                    raise CanvasMcpError(str(parsed["error"]))
                if include_headers:
                    return parsed, dict(response.headers.items())
                return parsed
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore")
            raise CanvasMcpError(
                f"Canvas MCP HTTP error {exc.code}: {body or exc.reason}"
            ) from exc
        except URLError as exc:
            raise CanvasMcpError(f"Canvas MCP connection error: {exc.reason}") from exc


_client: Optional[CanvasMcpClient] = None


def get_canvas_mcp_client() -> CanvasMcpClient:
    if not settings.use_canvas_mcp:
        raise CanvasMcpError(
            "Canvas MCP is disabled. Set USE_CANVAS_MCP=true to enable it."
        )
    if not settings.canvas_api_token or not settings.canvas_api_url:
        raise CanvasMcpError(
            "Canvas MCP credentials are incomplete. Set CANVAS_API_TOKEN and CANVAS_API_URL."
        )

    global _client
    if _client is None:
        _client = CanvasMcpClient()
    return _client


def list_canvas_tools() -> List[dict]:
    return get_canvas_mcp_client().list_tools()


def call_canvas_tool(tool_name: str, arguments: Optional[dict] = None) -> dict:
    return get_canvas_mcp_client().call_tool(tool_name=tool_name, arguments=arguments)


def summarize_canvas_tool_result(result: dict) -> str:
    structured_content = result.get("structuredContent")
    if structured_content:
        return json.dumps(structured_content)

    text_parts: List[str] = []
    for item in result.get("content", []):
        if item.get("type") == "text" and item.get("text"):
            text_parts.append(item["text"])

    if text_parts:
        return "\n".join(text_parts)

    return json.dumps(result)


def _decode_mcp_response_body(raw_body: str) -> dict:
    stripped = raw_body.strip()
    if not stripped:
        return {}

    if stripped.startswith("{"):
        return json.loads(stripped)

    data_lines: List[str] = []
    for line in stripped.splitlines():
        if line.startswith("data:"):
            payload = line[len("data:") :].strip()
            if payload:
                data_lines.append(payload)

    if not data_lines:
        raise CanvasMcpError("Canvas MCP response did not contain JSON data.")

    return json.loads("\n".join(data_lines))
