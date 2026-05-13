"""Plain-text session list."""

import click

from cockpit.store import collect_sessions


def format_size(b: int) -> str:
    if b < 1024:
        return f"{b}B"
    if b < 1024 * 1024:
        return f"{b / 1024:.0f}K"
    return f"{b / (1024 * 1024):.1f}M"


@click.command()
@click.option("-n", "--limit", default=50, help="Max sessions to show (0 = all).")
@click.option("--empty", is_flag=True, help="Include sessions with 0 turns.")
@click.option("--size", is_flag=True, help="Show disk usage per session.")
def list_cmd(limit: int, empty: bool, size: bool):
    """List sessions with turn counts."""
    sessions = collect_sessions(limit=limit, include_empty=empty, compute_disk=size)

    if not sessions:
        click.echo("No sessions found.")
        return

    for s in sessions:
        dot = "● " if s.active else "  "
        date = s.updated_at[:16].replace("T", " ") if s.updated_at else "?"
        branch = " ⑂" if s.is_branch else ""
        turns = f"[{s.turn_count}↻]"
        sz = f"  {format_size(s.disk_bytes)}" if size else ""
        click.echo(f"{dot}{date}  {turns:>6}  {s.display_name}{branch}{sz}  │  {s.display_cwd}")
