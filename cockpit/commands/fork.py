"""Fork (branch) a Copilot CLI session."""

from __future__ import annotations

import json
import shutil
import uuid

import click

from cockpit.store import STATE_DIR, collect_sessions, get_session


def _latest_session_id() -> str | None:
    sessions = collect_sessions(limit=1, include_empty=True)
    return sessions[0].id if sessions else None


def _rewrite_events(events_path, new_session_id: str, keep_turns: int | None = None):
    """Rewrite events.jsonl: update session ID and optionally truncate."""
    if not events_path.exists():
        return

    with open(events_path) as f:
        events = []
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    # Update session.start event
    for evt in events:
        if evt.get("type") == "session.start":
            evt.setdefault("data", {})["sessionId"] = new_session_id

    # Truncate to last N turns if requested
    if keep_turns is not None:
        user_indices = [i for i, e in enumerate(events) if e.get("type") == "user.message"]
        total = len(user_indices)

        if keep_turns < total:
            first_user = user_indices[0]
            keep_from = user_indices[-keep_turns]
            prefix = events[:first_user]
            suffix = events[keep_from:]
            events = prefix + suffix
            click.echo(f"Truncated: kept {keep_turns} of {total} turns ({len(events)} events)")
        else:
            click.echo(f"Only {total} turns exist, keeping all")

    with open(events_path, "w") as f:
        for evt in events:
            f.write(json.dumps(evt, separators=(",", ":")) + "\n")


def _reset_session_artifacts(session_dir):
    """Reset rewind snapshots, session DB, and checkpoints."""
    # Rewind snapshots
    rewind_dir = session_dir / "rewind-snapshots"
    if rewind_dir.is_dir():
        index = rewind_dir / "index.json"
        index.write_text('{"version":1,"snapshots":[],"filePathMap":{}}')
        backups = rewind_dir / "backups"
        if backups.is_dir():
            shutil.rmtree(backups)
            backups.mkdir()

    # Session database
    db = session_dir / "session.db"
    if db.exists():
        db.unlink()

    # Checkpoints
    ckpt_dir = session_dir / "checkpoints"
    if ckpt_dir.is_dir():
        (ckpt_dir / "index.md").write_text(
            "# Checkpoint History\n\n"
            "Checkpoints are listed in chronological order. "
            "Checkpoint 1 is the oldest, higher numbers are more recent.\n\n"
            "| # | Title | File |\n"
            "|---|-------|------|\n"
        )


@click.command()
@click.argument("session_id", required=False)
@click.option("-n", "--turns", type=int, default=None, help="Only keep the last N turns.")
def fork_cmd(session_id: str | None, turns: int | None):
    """Fork a session, creating an independent branch with shared history."""
    if not session_id:
        session_id = _latest_session_id()
        if not session_id:
            click.echo("No sessions found.", err=True)
            raise SystemExit(1)
        click.echo(f"Auto-selected latest session: {session_id}")

    source = get_session(session_id)
    if not source:
        click.echo(f"Session not found: {session_id}", err=True)
        raise SystemExit(1)

    source_dir = STATE_DIR / session_id
    new_id = str(uuid.uuid4())
    new_dir = STATE_DIR / new_id

    click.echo("Forking session...")
    shutil.copytree(source_dir, new_dir)

    # Update workspace.yaml
    ws_path = new_dir / "workspace.yaml"
    text = ws_path.read_text()
    lines = []
    for line in text.splitlines():
        if line.startswith("id: "):
            lines.append(f"id: {new_id}")
        else:
            lines.append(line)
    lines.append(f"branch_of: {session_id}")
    lines.append(f'branch_note: "Branched from: {source.display_name}"')
    ws_path.write_text("\n".join(lines) + "\n")

    # Rewrite events
    _rewrite_events(new_dir / "events.jsonl", new_id, keep_turns=turns)

    # Reset artifacts
    _reset_session_artifacts(new_dir)

    # Remove lock files
    for lock in new_dir.glob("inuse.*.lock"):
        lock.unlink()

    cwd = source.cwd or "."
    click.echo("")
    click.echo("Session forked successfully!")
    click.echo("")
    click.echo(f"New session: {new_id}")
    if source.summary:
        click.echo(f"From:        {source.display_name}")
    click.echo("")
    click.echo("To start the forked session:")
    click.echo("")
    click.echo(f"    cd {cwd} && copilot --resume={new_id}")
    click.echo("")
    click.echo("To return to the original:")
    click.echo("")
    click.echo(f"    copilot --resume={session_id}")
