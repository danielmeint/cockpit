"""Aggregate session statistics."""

from __future__ import annotations

from collections import Counter

import click

from cockpit.store import collect_sessions


def _format_size(b: int) -> str:
    if b < 1024:
        return f"{b}B"
    if b < 1024 * 1024:
        return f"{b / 1024:.0f}K"
    if b < 1024 * 1024 * 1024:
        return f"{b / (1024 * 1024):.1f}M"
    return f"{b / (1024 * 1024 * 1024):.1f}G"


@click.command()
def stats_cmd():
    """Show aggregate session statistics."""
    sessions = collect_sessions(limit=0, include_empty=True, compute_disk=True)

    if not sessions:
        click.echo("No sessions found.")
        return

    total = len(sessions)
    empty = sum(1 for s in sessions if s.is_empty)
    active = sum(1 for s in sessions if s.active)
    branches = sum(1 for s in sessions if s.is_branch)
    total_turns = sum(s.turn_count for s in sessions)
    total_bytes = sum(s.disk_bytes for s in sessions)
    empty_bytes = sum(s.disk_bytes for s in sessions if s.is_empty)

    click.echo("═══ Cockpit Stats ═══")
    click.echo("")
    click.echo(f"Sessions:     {total}")
    click.echo(f"  Active:     {active}")
    click.echo(f"  Empty:      {empty} ({_format_size(empty_bytes)})")
    click.echo(f"  Branches:   {branches}")
    click.echo(f"Total turns:  {total_turns}")
    click.echo(f"Disk usage:   {_format_size(total_bytes)}")
    click.echo("")

    # By repository
    repos: Counter[str] = Counter()
    for s in sessions:
        repos[s.repository or "(none)"] += 1
    click.echo("─── By repository ───")
    for repo, count in repos.most_common(10):
        click.echo(f"  {count:4d}  {repo}")
    click.echo("")

    # Largest sessions
    by_size = sorted(sessions, key=lambda s: s.disk_bytes, reverse=True)[:5]
    click.echo("─── Largest sessions ───")
    for s in by_size:
        click.echo(f"  {_format_size(s.disk_bytes):>6}  [{s.turn_count}↻]  {s.display_name}  │  {s.display_cwd}")

    # By month
    months: Counter[str] = Counter()
    for s in sessions:
        ts = s.updated_at or s.created_at
        if ts and len(ts) >= 7:
            months[ts[:7]] += 1
    if months:
        click.echo("")
        click.echo("─── By month ───")
        for month in sorted(months.keys(), reverse=True)[:6]:
            click.echo(f"  {month}  {months[month]:4d} sessions")
