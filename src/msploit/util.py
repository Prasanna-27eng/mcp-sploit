"""Small shared helpers used across modules."""
from __future__ import annotations

from typing import Any


def extract_text(result: dict[str, Any]) -> str:
    """Pull the human-readable text out of an MCP tools/call result."""
    content = result.get("content")
    if isinstance(content, list):
        texts = [item.get("text", "") for item in content if isinstance(item, dict)]
        return "\n".join(texts)
    return str(result)
