from __future__ import annotations

import pytest

from msploit.base import OptionValidationError
from msploit.framework import ModuleRegistry


@pytest.fixture()
def registry() -> ModuleRegistry:
    reg = ModuleRegistry()
    reg.load_modules()
    return reg


def test_module_loading(registry: ModuleRegistry) -> None:
    assert "exploit/mcp/file_exfiltration" in registry.modules
    assert "exploit/mcp/shell_exec" in registry.modules
    assert "exploit/mcp/prompt_injection" in registry.modules
    assert "exploit/mcp/tool_schema_abuse" in registry.modules
    assert "auxiliary/scanner/mcp_enum" in registry.modules
    assert "auxiliary/scanner/mcp_auth_bypass" in registry.modules
    assert "auxiliary/scanner/mcp_policy_probe" in registry.modules


def test_search(registry: ModuleRegistry) -> None:
    results = registry.search("file")
    assert "exploit/mcp/file_exfiltration" in results


def test_module_options_validation(registry: ModuleRegistry) -> None:
    module = registry.get_module("exploit/mcp/file_exfiltration")

    # TARGET is required and unset by default.
    with pytest.raises(OptionValidationError):
        module.validate_options()

    module.set_option("TARGET", "http://localhost:8765")
    module.validate_options()  # should not raise

    # FILE and TOOL have defaults, so they're already populated.
    assert module.get_option("FILE") == "/etc/passwd"
    assert module.get_option("TOOL") == "read_file"


def test_unknown_option_rejected(registry: ModuleRegistry) -> None:
    module = registry.get_module("exploit/mcp/file_exfiltration")
    with pytest.raises(OptionValidationError):
        module.set_option("NOPE", "value")


def test_check_does_not_send_exploit_payload(registry: ModuleRegistry, monkeypatch: pytest.MonkeyPatch) -> None:
    """check() must only call tools/list — never tools/call."""
    module = registry.get_module("exploit/mcp/file_exfiltration")
    module.set_option("TARGET", "http://localhost:8765")

    calls: list[str] = []

    class FakeClient:
        def list_tools(self):
            calls.append("tools/list")
            return [{"name": "read_file"}, {"name": "execute_shell"}]

        def call_tool(self, name, arguments=None):
            calls.append("tools/call")
            raise AssertionError("check() must not call tools/call")

    monkeypatch.setattr(module, "_client", lambda: FakeClient())

    assert module.check() is True
    assert calls == ["tools/list"]


def test_prompt_injection_check(registry: ModuleRegistry, monkeypatch: pytest.MonkeyPatch) -> None:
    module = registry.get_module("exploit/mcp/prompt_injection")
    module.set_option("TARGET", "http://localhost:8765")

    class FakeClient:
        def list_tools(self):
            return [{"name": "web_fetch"}, {"name": "execute_shell"}]

        def call_tool(self, name, arguments=None):
            raise AssertionError("check() must not call tools/call")

    monkeypatch.setattr(module, "_client", lambda: FakeClient())

    assert module.check() is True


def test_tool_schema_abuse_check(registry: ModuleRegistry, monkeypatch: pytest.MonkeyPatch) -> None:
    module = registry.get_module("exploit/mcp/tool_schema_abuse")
    module.set_option("TARGET", "http://localhost:8765")

    class FakeClient:
        def list_tools(self):
            return [
                {"name": "search_logs", "inputSchema": {"properties": {"query": {"type": "string"}}}},
            ]

        def call_tool(self, name, arguments=None):
            raise AssertionError("check() must not call tools/call")

    monkeypatch.setattr(module, "_client", lambda: FakeClient())

    assert module.check() is True


def test_mcp_auth_bypass_run(registry: ModuleRegistry, monkeypatch: pytest.MonkeyPatch) -> None:
    module = registry.get_module("auxiliary/scanner/mcp_auth_bypass")
    module.set_option("TARGET", "http://localhost:8765")

    class FakeClient:
        def initialize(self):
            return {"result": {"serverInfo": {"name": "vulnerable-mcp"}}}

        def list_tools(self):
            return [{"name": "read_file"}, {"name": "execute_shell"}]

    monkeypatch.setattr(module, "_client", lambda: FakeClient())

    output = module.run()
    assert "VULNERABLE" in output


def test_mcp_policy_probe_run(registry: ModuleRegistry, monkeypatch: pytest.MonkeyPatch) -> None:
    module = registry.get_module("auxiliary/scanner/mcp_policy_probe")
    module.set_option("TARGET", "http://localhost:8766")

    from msploit.mcp_client import MCPError

    class FakeClient:
        def call_tool(self, name, arguments=None):
            if name == "execute_shell":
                raise MCPError(-32600, "Shell execution tools are blocked")
            return {"content": [{"type": "text", "text": "ok"}]}

    monkeypatch.setattr(module, "_client", lambda: FakeClient())

    output = module.run()
    assert "[BLOCKED]" in output
    assert "[ALLOWED]" in output
