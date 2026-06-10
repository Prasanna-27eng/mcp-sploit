"""ModuleRegistry — discovers and instantiates modules under msploit.modules."""
from __future__ import annotations

import importlib
import pkgutil
from typing import Iterator

from msploit.base import Module

_MODULES_PACKAGE = "msploit.modules"


class ModuleRegistry:
    def __init__(self) -> None:
        self.modules: dict[str, type[Module]] = {}

    def load_modules(self, package: str = _MODULES_PACKAGE) -> None:
        """Recursively import every module under `package` and register any
        Module subclass that declares a non-empty `name`."""
        pkg = importlib.import_module(package)
        for _finder, mod_name, is_pkg in pkgutil.walk_packages(pkg.__path__, prefix=package + "."):
            if is_pkg:
                continue
            mod = importlib.import_module(mod_name)
            for attr in vars(mod).values():
                if (
                    isinstance(attr, type)
                    and issubclass(attr, Module)
                    and attr.__module__ == mod.__name__
                    and getattr(attr, "name", "")
                ):
                    self.modules[attr.name] = attr

    def get_module(self, path: str) -> Module:
        try:
            cls = self.modules[path]
        except KeyError as exc:
            raise KeyError(f"No such module: {path}") from exc
        return cls()

    def search(self, keyword: str) -> list[str]:
        keyword = keyword.lower()
        return sorted(p for p in self.modules if keyword in p.lower())

    def __iter__(self) -> Iterator[str]:
        return iter(sorted(self.modules))

    def __len__(self) -> int:
        return len(self.modules)
