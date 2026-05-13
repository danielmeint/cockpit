"""Session discovery and parsing."""

from __future__ import annotations

import glob
import json
import os
from pathlib import Path

from cockpit.models import Session

STATE_DIR = Path(os.path.expanduser("~/.copilot/session-state"))


def parse_workspace(path: Path) -> dict[str, str]:
    fields: dict[str, str] = {}
    try:
        with open(path) as f:
            for line in f:
                line = line.rstrip()
                if ": " in line:
                    key, val = line.split(": ", 1)
                    fields[key] = val
    except OSError:
        pass
    return fields


def count_turns(session_dir: Path) -> int:
    events_path = session_dir / "events.jsonl"
    if not events_path.exists():
        return 0
    count = 0
    try:
        with open(events_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    evt = json.loads(line)
                    if evt.get("type") == "user.message":
                        count += 1
                except json.JSONDecodeError:
                    continue
    except OSError:
        pass
    return count


def get_last_user_message(session_dir: Path, max_length: int = 500) -> str:
    events_path = session_dir / "events.jsonl"
    if not events_path.exists():
        return ""
    last_msg = ""
    try:
        with open(events_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    evt = json.loads(line)
                    if evt.get("type") == "user.message":
                        last_msg = evt.get("data", {}).get("content", "")
                except json.JSONDecodeError:
                    continue
    except OSError:
        pass
    if len(last_msg) > max_length:
        last_msg = last_msg[:max_length] + "…"
    return last_msg


def dir_size(path: Path) -> int:
    total = 0
    try:
        for entry in path.rglob("*"):
            if entry.is_file():
                total += entry.stat().st_size
    except OSError:
        pass
    return total


def find_active_sessions() -> dict[str, int]:
    active: dict[str, int] = {}
    for lock in glob.glob(str(STATE_DIR / "*/inuse.*.lock")):
        fname = os.path.basename(lock)
        parts = fname.split(".")
        if len(parts) < 3:
            continue
        try:
            pid = int(parts[1])
        except ValueError:
            continue
        sid = os.path.basename(os.path.dirname(lock))
        try:
            os.kill(pid, 0)
            active[sid] = pid
        except ProcessLookupError:
            pass
        except PermissionError:
            active[sid] = pid
    return active


def collect_sessions(
    *,
    limit: int = 50,
    include_empty: bool = False,
    compute_disk: bool = False,
) -> list[Session]:
    if not STATE_DIR.is_dir():
        return []

    active = find_active_sessions()
    sessions: list[Session] = []

    for ws_path in STATE_DIR.glob("*/workspace.yaml"):
        session_dir = ws_path.parent
        fields = parse_workspace(ws_path)
        sid = fields.get("id", session_dir.name)
        turns = count_turns(session_dir)

        if not include_empty and turns == 0:
            continue

        sessions.append(
            Session(
                id=sid,
                cwd=fields.get("cwd", ""),
                summary=fields.get("summary", ""),
                name=fields.get("name", ""),
                updated_at=fields.get("updated_at", fields.get("created_at", "")),
                created_at=fields.get("created_at", ""),
                branch_of=fields.get("branch_of", ""),
                branch_note=fields.get("branch_note", ""),
                repository=fields.get("repository", ""),
                branch=fields.get("branch", ""),
                active=sid in active,
                pid=active.get(sid),
                turn_count=turns,
                disk_bytes=dir_size(session_dir) if compute_disk else 0,
            )
        )

    # Active first, then by recency
    sessions.sort(key=lambda s: (s.active, s.updated_at), reverse=True)

    if limit > 0:
        sessions = sessions[:limit]
    return sessions


def get_session(session_id: str) -> Session | None:
    session_dir = STATE_DIR / session_id
    ws_path = session_dir / "workspace.yaml"
    if not ws_path.exists():
        return None

    active = find_active_sessions()
    fields = parse_workspace(ws_path)
    sid = fields.get("id", session_dir.name)

    return Session(
        id=sid,
        cwd=fields.get("cwd", ""),
        summary=fields.get("summary", ""),
        name=fields.get("name", ""),
        updated_at=fields.get("updated_at", fields.get("created_at", "")),
        created_at=fields.get("created_at", ""),
        branch_of=fields.get("branch_of", ""),
        branch_note=fields.get("branch_note", ""),
        repository=fields.get("repository", ""),
        branch=fields.get("branch", ""),
        active=sid in active,
        pid=active.get(sid),
        turn_count=count_turns(session_dir),
        disk_bytes=dir_size(session_dir),
    )


def delete_session(session_id: str) -> int:
    """Delete a session directory. Returns freed bytes."""
    import shutil

    session_dir = STATE_DIR / session_id
    if not session_dir.is_dir():
        return 0
    size = dir_size(session_dir)
    shutil.rmtree(session_dir)
    return size
