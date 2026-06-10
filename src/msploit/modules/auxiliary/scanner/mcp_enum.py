"""auxiliary/scanner/mcp_enum — enumerate tools exposed by an MCP server."""
from __future__ import annotations

from msploit.base import TARGET_OPTION, AuxiliaryModule

_DANGEROUS_HINTS = ("shell", "exec", "bash", "command", "terminal", "subprocess", "eval", "read_file", "write_file")


class MCPEnum(AuxiliaryModule):
    name = "auxiliary/scanner/mcp_enum"
    description = "Enumerate tools exposed by an MCP server via tools/list and flag high-risk tool names."
    author = "Prasanna Kumar Surendran"
    options = (TARGET_OPTION,)

    def run(self) -> str:
        target = self.get_option("TARGET")
        client = self._client()

        lines = [f"[*] Connecting to {target}...", "[*] Sending tools/list request..."]
        tools = client.list_tools()
        lines.append(f"[+] {len(tools)} tool(s) exposed:")
        for tool in tools:
            tool_name = tool.get("name", "?")
            description = tool.get("description", "")
            flag = " [!] HIGH RISK" if any(hint in tool_name.lower() for hint in _DANGEROUS_HINTS) else ""
            lines.append(f"    - {tool_name}: {description}{flag}")
        return "\n".join(lines)
