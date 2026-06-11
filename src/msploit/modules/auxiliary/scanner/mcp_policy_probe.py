"""auxiliary/scanner/mcp_policy_probe — fingerprint an mcp-aegis-style
gateway's effective policy by probing a battery of representative tool calls."""
from __future__ import annotations

from typing import Any

from msploit.base import TARGET_OPTION, AuxiliaryModule
from msploit.mcp_client import MCPError
from msploit.util import extract_text

# (label, tool, arguments) — chosen to mirror mcp-aegis's default policy
# rule categories (block_shell_execution, block_credential_reads,
# log_home_directory_crawl, log_network_requests,
# log_git_credential_exposure, log_database_writes, default_allow).
_PROBES: tuple[tuple[str, str, dict[str, Any]], ...] = (
    ("shell_execution", "execute_shell", {"command": "id"}),
    ("credential_read_ssh", "read_file", {"path": "~/.ssh/id_rsa"}),
    ("credential_read_env", "read_file", {"path": ".env"}),
    ("home_directory_crawl", "list_files", {"path": "~"}),
    ("network_request", "http_request", {"url": "http://169.254.169.254/latest/meta-data/"}),
    ("git_credential_exposure", "read_file", {"path": ".git/config"}),
    ("database_write", "execute_sql", {"query": "DROP TABLE users"}),
    ("benign_read", "read_file", {"path": "/etc/hostname"}),
)


class MCPPolicyProbe(AuxiliaryModule):
    name = "auxiliary/scanner/mcp_policy_probe"
    description = (
        "Sends a battery of representative tool calls (shell exec, "
        "credential reads, home directory crawl, network/database access) "
        "and reports whether each is BLOCKED, forwarded, or executed — "
        "fingerprinting the effective policy of an mcp-aegis (or similar) "
        "gateway."
    )
    author = "Prasanna Kumar Surendran"
    references = ("https://github.com/Prasanna-27eng/mcp-aegis",)
    options = (TARGET_OPTION,)

    def run(self) -> str:
        target = self.get_option("TARGET")
        client = self._client()

        lines = [f"[*] Probing policy at {target} with {len(_PROBES)} representative call(s)..."]
        for label, tool, args in _PROBES:
            lines.append(f"\n[*] {label}: tools/call {tool} {args}")
            try:
                result = client.call_tool(tool, args)
            except MCPError as exc:
                if exc.code == -32600:
                    lines.append(f"    [BLOCKED] policy rejected the call — {exc.message}")
                else:
                    lines.append(f"    [ERROR {exc.code}] {exc.message}")
                continue

            if result.get("isError"):
                lines.append(f"    [ALLOWED-NOOP] forwarded but tool returned an error: {extract_text(result)[:100]!r}")
            else:
                lines.append(f"    [ALLOWED] forwarded and executed: {extract_text(result)[:100]!r}")

        return "\n".join(lines)
