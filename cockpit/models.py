"""Session data model."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class Session:
    id: str
    cwd: str = ""
    summary: str = ""
    name: str = ""
    updated_at: str = ""
    created_at: str = ""
    branch_of: str = ""
    branch_note: str = ""
    repository: str = ""
    branch: str = ""
    active: bool = False
    pid: int | None = None
    turn_count: int = 0
    disk_bytes: int = 0

    @property
    def display_cwd(self) -> str:
        home = os.path.expanduser("~")
        return self.cwd.replace(home, "~") if self.cwd else "~"

    @property
    def display_name(self) -> str:
        return self.summary or self.name or "(no summary)"

    @property
    def is_empty(self) -> bool:
        return self.turn_count == 0

    @property
    def is_branch(self) -> bool:
        return bool(self.branch_of)
