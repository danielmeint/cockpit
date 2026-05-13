"""Preview helper for fzf — called as `python3 -m cockpit.preview <session_id>`."""

from __future__ import annotations

import sys

from cockpit.store import get_last_user_message, get_session, STATE_DIR


def format_size(b: int) -> str:
    if b < 1024:
        return f"{b}B"
    if b < 1024 * 1024:
        return f"{b / 1024:.0f}K"
    return f"{b / (1024 * 1024):.1f}M"


def main():
    if len(sys.argv) < 2:
        return
    sid = sys.argv[1]
    session = get_session(sid)
    if not session:
        print(f"Session not found: {sid}")
        return

    print(f"Turns: {session.turn_count}  │  Size: {format_size(session.disk_bytes)}")
    if session.repository:
        print(f"Repo:  {session.repository}  │  Branch: {session.branch}")
    if session.is_branch:
        print(f"Fork of: {session.branch_of}")
    last = get_last_user_message(STATE_DIR / sid)
    if last:
        print(f"─── last message ───")
        print(last)
    else:
        print("(no messages)")


if __name__ == "__main__":
    main()
