"""auxiliary/scanner/mcp_auth_bypass — check whether the target enforces
any authentication on the MCP initialize/tools-list handshake."""
from __future__ import annotations

from msploit.base import TARGET_OPTION, AuxiliaryModule
from msploit.mcp_client import MCPError


class MCPAuthBypass(AuxiliaryModule):
    name = "auxiliary/scanner/mcp_auth_bypass"
    description = (
        "Sends an unauthenticated initialize + tools/list handshake (no "
        "credentials, no API key) and reports whether the target accepts it."
    )
    author = "Prasanna Kumar Surendran"
    references = (
        "https://github.com/Prasanna-27eng/mcp-aegis",
        "CWE-306 - Missing Authentication for Critical Function",
    )
    options = (TARGET_OPTION,)

    def run(self) -> str:
        target = self.get_option("TARGET")
        client = self._client()

        lines = [f"[*] Connecting to {target} with no credentials...", "[*] Sending initialize..."]
        try:
            init = client.initialize()
        except MCPError as exc:
            lines.append(f"[-] initialize rejected: {exc}")
            lines.append("[+] Target appears to enforce authentication on initialize.")
            return "\n".join(lines)

        server_info = init.get("result", {}).get("serverInfo", {})
        lines.append(f"[+] initialize succeeded with no credentials. Server: {server_info}")

        lines.append("[*] Sending tools/list...")
        try:
            tools = client.list_tools()
        except MCPError as exc:
            lines.append(f"[-] tools/list rejected: {exc}")
            lines.append("[+] Target enforces authentication on tools/list, even though initialize is open.")
            return "\n".join(lines)

        lines.append(f"[+] tools/list succeeded with no credentials. {len(tools)} tool(s) exposed.")
        lines.append(
            "[!] VULNERABLE: target accepts the full MCP handshake (initialize "
            "+ tools/list) with no authentication — any client that can reach "
            "this endpoint can enumerate and call its tools."
        )
        return "\n".join(lines)
