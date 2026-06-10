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
    assert "auxiliary/scanner/mcp_enum" in registry.modules


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
