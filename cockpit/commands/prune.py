"""Prune empty and old sessions."""

from __future__ import annotations

from datetime import UTC, datetime

import click

from cockpit.store import collect_sessions, delete_session


def _format_size(b: int) -> str:
    if b < 1024:
        return f"{b}B"
    if b < 1024 * 1024:
        return f"{b / 1024:.0f}K"
    return f"{b / (1024 * 1024):.1f}M"


def _parse_age(age_str: str) -> int:
    """Parse age string like '30d', '2w', '6h' into seconds."""
    units = {"h": 3600, "d": 86400, "w": 604800}
    suffix = age_str[-1].lower()
    if suffix not in units:
        raise click.BadParameter(f"Unknown unit '{suffix}'. Use h/d/w (e.g. 30d, 2w).")
    try:
        value = int(age_str[:-1])
    except ValueError as exc:
        raise click.BadParameter(f"Invalid number in '{age_str}'.") from exc
    return value * units[suffix]


@click.command()
@click.option("--older-than", default=None, help="Only prune sessions older than this (e.g. 30d, 2w).")
@click.option("--dry-run", is_flag=True, help="Show what would be deleted without deleting.")
@click.option("--force", is_flag=True, help="Delete without confirmation.")
def prune_cmd(older_than: str | None, dry_run: bool, force: bool):
    """Delete empty sessions (0 turns) to free disk space."""
    sessions = collect_sessions(limit=0, include_empty=True, compute_disk=True)

    candidates = [s for s in sessions if s.is_empty and not s.active]

    if older_than:
        max_age_secs = _parse_age(older_than)
        now = datetime.now(UTC)
        filtered = []
        for s in candidates:
            ts = s.updated_at or s.created_at
            if not ts:
                filtered.append(s)
                continue
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                if (now - dt).total_seconds() > max_age_secs:
                    filtered.append(s)
            except ValueError:
                filtered.append(s)
        candidates = filtered

    if not candidates:
        click.echo("No empty sessions to prune.")
        return

    total_bytes = sum(s.disk_bytes for s in candidates)
    click.echo(f"Found {len(candidates)} empty session(s) ({_format_size(total_bytes)}):")
    click.echo("")

    for s in candidates[:20]:
        date = s.updated_at[:16].replace("T", " ") if s.updated_at else "?"
        click.echo(f"  {date}  {_format_size(s.disk_bytes):>5}  {s.display_name}  │  {s.display_cwd}")
    if len(candidates) > 20:
        click.echo(f"  ... and {len(candidates) - 20} more")

    if dry_run:
        click.echo(f"\nDry run — would free {_format_size(total_bytes)}.")
        return

    if not force:
        click.echo("")
        click.confirm(f"Delete {len(candidates)} session(s) and free {_format_size(total_bytes)}?", abort=True)

    freed = 0
    for s in candidates:
        freed += delete_session(s.id)

    click.echo(f"\nDeleted {len(candidates)} session(s), freed {_format_size(freed)}.")
