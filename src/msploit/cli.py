"""mcp-sploit interactive console — a Metasploit-style REPL for MCP modules."""
from __future__ import annotations

import cmd
import shlex
import sys

from msploit import __version__
from msploit.base import Module, OptionValidationError
from msploit.framework import ModuleRegistry

BANNER = rf"""
 _ __ ___   ___ _ __    ___ _ __ | | ___(_) |_
| '_ ` _ \ / __| '_ \  / __| '_ \| |/ _ \ | __|
| | | | | | (__| |_) | \__ \ |_) | | (_) | |_
|_| |_| |_|\___| .__/  |___/ .__/|_|\___/_|\__|
               |_|         |_|

mcp-sploit v{__version__} — MCP exploitation framework
Type 'help' for a list of commands, 'show modules' to list modules.
"""


class MsploitShell(cmd.Cmd):
    intro = BANNER
    prompt = "mcp-sploit > "

    def __init__(self) -> None:
        super().__init__()
        self.registry = ModuleRegistry()
        self.registry.load_modules()
        self.current: Module | None = None

    # ------------------------------------------------------------------
    def _set_prompt(self) -> None:
        if self.current is None:
            self.prompt = "mcp-sploit > "
        else:
            self.prompt = f"mcp-sploit {self.current.kind}({self.current.name}) > "

    # ------------------------------------------------------------------
    # Module browsing
    # ------------------------------------------------------------------
    def do_show(self, arg: str) -> None:
        """show modules|exploits|auxiliary|options — list modules or current options"""
        arg = arg.strip().lower()
        if arg in ("modules", "all", ""):
            for path in self.registry:
                print(path)
        elif arg == "exploits":
            for path in self.registry:
                if path.startswith("exploit/"):
                    print(path)
        elif arg == "auxiliary":
            for path in self.registry:
                if path.startswith("auxiliary/"):
                    print(path)
        elif arg == "options":
            if not self.current:
                print("[-] No module selected. Use 'use <module>' first.")
                return
            print(f"\nModule options ({self.current.name}):\n")
            print(self.current.show_options())
            print()
        else:
            print("Usage: show modules|exploits|auxiliary|options")

    def do_search(self, arg: str) -> None:
        """search <keyword> — search module paths"""
        keyword = arg.strip()
        if not keyword:
            print("Usage: search <keyword>")
            return
        results = self.registry.search(keyword)
        if not results:
            print("[-] No matching modules.")
            return
        for path in results:
            print(path)

    def do_use(self, arg: str) -> None:
        """use <module/path> — select a module"""
        path = arg.strip()
        if not path:
            print("Usage: use <module/path>")
            return
        try:
            self.current = self.registry.get_module(path)
        except KeyError as exc:
            print(f"[-] {exc}")
            return
        self._set_prompt()
        print(f"[*] Using {self.current.kind} module: {self.current.name}")

    def do_back(self, arg: str) -> None:
        """back — clear the current module context"""
        self.current = None
        self._set_prompt()

    def do_info(self, arg: str) -> None:
        """info — show details about the current module"""
        if not self.current:
            print("[-] No module selected.")
            return
        print()
        print(self.current.info())
        print()

    # ------------------------------------------------------------------
    # Option handling
    # ------------------------------------------------------------------
    def do_set(self, arg: str) -> None:
        """set <OPTION> <value> — set an option on the current module"""
        if not self.current:
            print("[-] No module selected.")
            return
        parts = shlex.split(arg)
        if len(parts) < 2:
            print("Usage: set <OPTION> <value>")
            return
        key, value = parts[0], " ".join(parts[1:])
        try:
            self.current.set_option(key, value)
        except OptionValidationError as exc:
            print(f"[-] {exc}")
            return
        print(f"{key.upper()} => {value}")

    def do_unset(self, arg: str) -> None:
        """unset <OPTION> — reset an option to its default"""
        if not self.current:
            print("[-] No module selected.")
            return
        key = arg.strip()
        if not key:
            print("Usage: unset <OPTION>")
            return
        try:
            self.current.unset_option(key)
        except OptionValidationError as exc:
            print(f"[-] {exc}")
            return
        print(f"Unsetting {key.upper()}")

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------
    def do_check(self, arg: str) -> None:
        """check — run the module's safe vulnerability check (no payload sent)"""
        if not self.current:
            print("[-] No module selected.")
            return
        if not hasattr(self.current, "check"):
            print("[-] This module does not implement check().")
            return
        try:
            self.current.validate_options()
        except OptionValidationError as exc:
            print(f"[-] {exc}")
            return
        try:
            self.current.check()
        except Exception as exc:  # noqa: BLE001 - surface any failure to the operator
            print(f"[-] Check failed: {exc}")

    def do_exploit(self, arg: str) -> None:
        """exploit / run — execute the current module"""
        self._run_current()

    def do_run(self, arg: str) -> None:
        """run / exploit — execute the current module"""
        self._run_current()

    def _run_current(self) -> None:
        if not self.current:
            print("[-] No module selected.")
            return
        try:
            self.current.validate_options()
        except OptionValidationError as exc:
            print(f"[-] {exc}")
            return
        try:
            if hasattr(self.current, "exploit"):
                output = self.current.exploit()
            else:
                output = self.current.run()
            print(output)
        except Exception as exc:  # noqa: BLE001 - keep the console alive on module errors
            print(f"[-] Module execution failed: {exc}")

    # ------------------------------------------------------------------
    # Housekeeping
    # ------------------------------------------------------------------
    def do_exit(self, arg: str) -> bool:
        """exit / quit — leave mcp-sploit"""
        return True

    def do_quit(self, arg: str) -> bool:
        """exit / quit — leave mcp-sploit"""
        return True

    def do_EOF(self, arg: str) -> bool:
        print()
        return True

    def emptyline(self) -> None:
        pass


def main() -> None:
    shell = MsploitShell()
    try:
        shell.cmdloop()
    except KeyboardInterrupt:
        print()
        sys.exit(0)


if __name__ == "__main__":
    main()
