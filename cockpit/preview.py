"""Preview helper for fzf — called as `python3 -m cockpit.preview <session_id>`."""

from __future__ import annotations

import json
import sys

from cockpit.store import STATE_DIR, get_session

_BOLD = "\033[1m"
_DIM = "\033[2m"
_CYAN = "\033[36m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_RESET = "\033[0m"


def format_size(b: int) -> str:
    if b < 1024:
        return f"{b}B"
    if b < 1024 * 1024:
        return f"{b / 1024:.0f}K"
    return f"{b / (1024 * 1024):.1f}M"


def get_last_messages(session_dir, count: int = 2, max_length: int = 300) -> list[tuple[str, str]]:
    """Return last N (role, content) pairs from events, skipping empty messages."""
    events_path = session_dir / "events.jsonl"
    if not events_path.exists():
        return []
    messages: list[tuple[str, str]] = []
    try:
        with open(events_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    evt = json.loads(line)
                except json.JSONDecodeError:
                    continue
                etype = evt.get("type", "")
                if etype == "user.message":
                    content = evt.get("data", {}).get("content", "")
                    if content.strip():
                        messages.append(("user", content))
                elif etype == "assistant.message":
                    content = evt.get("data", {}).get("content", "")
                    if content.strip():
                        messages.append(("assistant", content))
    except OSError:
        pass
    result = messages[-count:] if len(messages) > count else messages
    truncated = []
    for role, content in result:
        content = content.replace("\n", " ").strip()
        if len(content) > max_length:
            content = content[:max_length] + "…"
        truncated.append((role, content))
    return truncated


def main():
    if len(sys.argv) < 2:
        return
    sid = sys.argv[1]
    session = get_session(sid)
    if not session:
        print(f"Session not found: {sid}")
        return

    # Header line
    parts = [f"{_CYAN}Turns: {session.turn_count}{_RESET}", f"Size: {format_size(session.disk_bytes)}"]
    if session.active:
        parts.insert(0, f"{_GREEN}● ACTIVE{_RESET}")
    print("  │  ".join(parts))

    if session.repository:
        print(f"{_DIM}Repo:  {session.repository}  │  Branch: {session.branch}{_RESET}")
    if session.is_branch:
        print(f"{_DIM}Fork of: {session.branch_of}{_RESET}")

    messages = get_last_messages(STATE_DIR / sid)
    if messages:
        print(f"{_DIM}─── recent messages ───{_RESET}")
        for role, content in messages:
            if role == "user":
                print(f"{_YELLOW}▸ {content}{_RESET}")
            else:
                print(f"{_DIM}◂ {content}{_RESET}")
    else:
        print(f"{_DIM}(no messages){_RESET}")


if __name__ == "__main__":
    main()
