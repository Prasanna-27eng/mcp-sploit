"""target_server/app.py — intentionally vulnerable MCP server.

Speaks real JSON-RPC 2.0 / MCP (`initialize`, `tools/list`, `tools/call`) over
POST /, so it can be used standalone OR behind an mcp-aegis gateway with no
changes to either side.

DANGER: no authentication, no input validation, no path restrictions.
Only run inside the isolated docker-compose network in this repo.
"""
from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI(title="vulnerable-mcp")

TOOLS: list[dict[str, Any]] = [
    {
        "name": "read_file",
        "description": "Read the contents of a file on the host filesystem.",
        "inputSchema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    },
    {
        "name": "execute_shell",
        "description": "Execute a shell command on the host.",
        "inputSchema": {
            "type": "object",
            "properties": {"command": {"type": "string"}},
            "required": ["command"],
        },
    },
]


def _text_result(text: str, is_error: bool = False) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": text}], "isError": is_error}


def _call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if name == "read_file":
        # DANGEROUS: blindly reads any path the caller asks for.
        path = arguments.get("path", "/etc/passwd")
        try:
            with open(path, "r") as fh:
                return _text_result(fh.read())
        except OSError as exc:
            return _text_result(str(exc), is_error=True)

    if name == "execute_shell":
        # DANGEROUS: blindly executes any shell command the caller asks for.
        command = arguments.get("command", "id")
        return _text_result(os.popen(command).read())

    return _text_result(f"Unknown tool: {name}", is_error=True)


@app.post("/")
async def rpc_endpoint(request: Request) -> JSONResponse:
    envelope = await request.json()
    method: str = envelope.get("method", "")
    params: dict[str, Any] = envelope.get("params") or {}
    request_id = envelope.get("id")

    if method == "initialize":
        result: dict[str, Any] = {
            "protocolVersion": "2024-11-05",
            "serverInfo": {"name": "vulnerable-mcp", "version": "0.1.0"},
            "capabilities": {"tools": {}},
        }
    elif method == "tools/list":
        result = {"tools": TOOLS}
    elif method == "tools/call":
        result = _call_tool(params.get("name", ""), params.get("arguments") or {})
    else:
        return JSONResponse(
            {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": f"Method not found: {method}"}}
        )

    return JSONResponse({"jsonrpc": "2.0", "id": request_id, "result": result})


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
