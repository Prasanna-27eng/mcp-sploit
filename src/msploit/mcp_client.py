"""Minimal JSON-RPC 2.0 client for the MCP tools/call protocol.

Speaks to a raw MCP server OR an mcp-aegis gateway sitting in front of one —
both accept the same JSON-RPC envelope at POST /.
"""
from __future__ import annotations

import itertools
import uuid
from typing import Any

import httpx


class MCPError(Exception):
    """Raised when the target returns a JSON-RPC error envelope.

    This covers both genuine upstream errors and gateway BLOCK responses
    (e.g. mcp-aegis returns code -32600 with the policy reason as message).
    """

    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")


class MCPClient:
    def __init__(self, base_url: str, timeout: float = 10.0, session_id: str | None = None) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._session_id = session_id or str(uuid.uuid4())
        self._id_counter = itertools.count(1)

    @property
    def session_id(self) -> str:
        return self._session_id

    def _request(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        envelope = {
            "jsonrpc": "2.0",
            "id": next(self._id_counter),
            "method": method,
            "params": params or {},
        }
        headers = {"Content-Type": "application/json", "X-MCP-Session-ID": self._session_id}
        response = httpx.post(self._base_url + "/", json=envelope, headers=headers, timeout=self._timeout)
        response.raise_for_status()
        return response.json()

    def initialize(self) -> dict[str, Any]:
        return self._request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "mcp-sploit", "version": "0.1.0"},
            },
        )

    def list_tools(self) -> list[dict[str, Any]]:
        envelope = self._request("tools/list")
        if "error" in envelope:
            err = envelope["error"]
            raise MCPError(err.get("code", -1), err.get("message", "unknown error"))
        return envelope.get("result", {}).get("tools", [])

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        envelope = self._request("tools/call", {"name": name, "arguments": arguments or {}})
        if "error" in envelope:
            err = envelope["error"]
            raise MCPError(err.get("code", -1), err.get("message", "unknown error"))
        return envelope.get("result", {})
