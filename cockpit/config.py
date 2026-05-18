"""User configuration loading."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

CONFIG_PATH = Path(os.environ.get("COCKPIT_CONFIG", "~/.config/cockpit/config.toml")).expanduser()


@dataclass
class Config:
    copilot_args: list[str] = field(default_factory=list)

    @classmethod
    def load(cls) -> Config:
        if not CONFIG_PATH.exists():
            return cls()
        try:
            import tomllib
        except ModuleNotFoundError:
            import tomli as tomllib  # type: ignore[no-redef]

        try:
            with open(CONFIG_PATH, "rb") as f:
                data = tomllib.load(f)
        except Exception:
            return cls()

        return cls(
            copilot_args=data.get("copilot_args", []),
        )
