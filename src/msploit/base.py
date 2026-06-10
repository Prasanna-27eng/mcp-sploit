"""Base classes for msploit modules: options, validation, and the
exploit/auxiliary contracts that the CLI and ModuleRegistry rely on.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from msploit.mcp_client import MCPClient


class OptionValidationError(ValueError):
    """Raised when required options are missing or an unknown option is set."""


@dataclass(frozen=True)
class Option:
    name: str
    description: str
    required: bool = True
    default: Any = None


# Every module talks to a TARGET — either a raw MCP server or an mcp-aegis
# gateway URL sitting in front of one. Shared so all modules expose it
# identically.
TARGET_OPTION = Option(
    name="TARGET",
    description="The MCP server URL (or mcp-aegis gateway URL)",
    required=True,
)


class Module:
    """Common base for exploit and auxiliary modules."""

    name: str = ""
    description: str = ""
    author: str = ""
    references: tuple[str, ...] = ()
    options: tuple[Option, ...] = ()
    kind: str = "module"

    def __init__(self) -> None:
        self._values: dict[str, Any] = {opt.name: opt.default for opt in self.options}

    # ------------------------------------------------------------------
    # Option handling
    # ------------------------------------------------------------------
    def set_option(self, key: str, value: str) -> None:
        key = key.upper()
        if key not in self._values:
            raise OptionValidationError(f"Unknown option: {key}")
        self._values[key] = value

    def unset_option(self, key: str) -> None:
        key = key.upper()
        if key not in self._values:
            raise OptionValidationError(f"Unknown option: {key}")
        opt = next(o for o in self.options if o.name == key)
        self._values[key] = opt.default

    def get_option(self, key: str) -> Any:
        return self._values.get(key.upper())

    def validate_options(self) -> None:
        missing = [opt.name for opt in self.options if opt.required and not self._values.get(opt.name)]
        if missing:
            raise OptionValidationError(f"Missing required option(s): {', '.join(missing)}")

    def show_options(self) -> str:
        header = f"{'Name':<10}{'Current Setting':<40}{'Required':<10}Description"
        lines = [header, "-" * len(header)]
        for opt in self.options:
            current = self._values.get(opt.name)
            current_str = "" if current is None else str(current)
            required_str = "yes" if opt.required else "no"
            lines.append(f"{opt.name:<10}{current_str:<40}{required_str:<10}{opt.description}")
        return "\n".join(lines)

    def info(self) -> str:
        lines = [
            f"       Name: {self.name}",
            f"     Module: {self.kind}",
            f"     Author: {self.author or 'unknown'}",
            f"Description: {self.description}",
        ]
        if self.references:
            lines.append("References:")
            lines.extend(f"  - {r}" for r in self.references)
        lines.append("")
        lines.append(self.show_options())
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Networking helper
    # ------------------------------------------------------------------
    def _client(self) -> MCPClient:
        target = self.get_option("TARGET")
        if not target:
            raise OptionValidationError("TARGET is not set")
        return MCPClient(target)


class AuxiliaryModule(Module):
    """Modules that gather information without claiming to exploit anything."""

    kind = "auxiliary"

    def run(self) -> str:
        raise NotImplementedError


class ExploitModule(Module):
    """Modules that demonstrate a concrete vulnerability against TARGET."""

    kind = "exploit"

    def check(self) -> bool:
        """Safe, side-effect-free probe. Must never send the exploit payload."""
        raise NotImplementedError

    def exploit(self) -> str:
        raise NotImplementedError
