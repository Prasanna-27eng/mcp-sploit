# Contributing to mcp-sploit

Contributions are welcome — especially new modules. The module system is
deliberately small so it's easy to add coverage for new MCP attack classes.

## Adding a module

1. Pick a path that follows the existing convention:
   - `auxiliary/scanner/<name>.py` — gathers information, no exploitation
     (subclass `AuxiliaryModule`, implement `run()`)
   - `exploit/mcp/<name>.py` — demonstrates a concrete vulnerability
     (subclass `ExploitModule`, implement `check()` and `exploit()`)
2. Set `name`, `description`, `author`, and `references` (CWE / ATT&CK /
   MITRE ATLAS IDs are encouraged — see existing modules for the format).
3. Declare `options` using `TARGET_OPTION` plus any module-specific `Option`s.
4. `check()` must be safe and side-effect-free — it should never send the
   actual exploit payload (e.g. only call `tools/list`, never `tools/call`
   with attacker-controlled arguments).
5. If your module needs a tool that doesn't exist on the bundled
   `target_server`, add a small mock implementation there so the module is
   testable end-to-end without touching real infrastructure.
6. Add tests to `tests/test_framework.py`: at minimum, that the module loads
   and that `check()` doesn't call `tools/call`.

## Ideas for new modules

Open an issue or check existing issues for module ideas — e.g. SQL injection
via a `execute_sql`-style tool, MCP `resources/read` path traversal, or
sampling/`createMessage` abuse.

## Running tests

```bash
pip install -e ".[dev]"
pytest
```

## Reporting a vulnerability in mcp-sploit itself

mcp-sploit is offensive tooling intended for use against your own
infrastructure or systems you have explicit permission to test. If you find
a bug that could cause mcp-sploit itself to be misused beyond its documented
scope, please open an issue describing the problem.
