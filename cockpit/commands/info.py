"""Detailed session info."""

from __future__ import annotations

import click

from cockpit.store import STATE_DIR, get_last_user_message, get_session


def _format_size(b: int) -> str:
    if b < 1024:
        return f"{b}B"
    if b < 1024 * 1024:
        return f"{b / 1024:.0f}K"
    return f"{b / (1024 * 1024):.1f}M"


@click.command()
@click.argument("session_id")
def info_cmd(session_id: str):
    """Show detailed information about a session."""
    session = get_session(session_id)
    if not session:
        click.echo(f"Session not found: {session_id}", err=True)
        raise SystemExit(1)

    dot = "● ACTIVE" if session.active else "  inactive"
    click.echo(f"Session:    {session.id}")
    click.echo(f"Status:     {dot}" + (f" (pid {session.pid})" if session.pid else ""))
    click.echo(f"Summary:    {session.display_name}")
    click.echo(f"Directory:  {session.display_cwd}")
    if session.repository:
        click.echo(f"Repository: {session.repository}")
    if session.branch:
        click.echo(f"Branch:     {session.branch}")
    click.echo(f"Turns:      {session.turn_count}")
    click.echo(f"Size:       {_format_size(session.disk_bytes)}")
    click.echo(f"Created:    {session.created_at}")
    click.echo(f"Updated:    {session.updated_at}")
    if session.is_branch:
        click.echo(f"Fork of:    {session.branch_of}")
        if session.branch_note:
            click.echo(f"Note:       {session.branch_note}")

    last = get_last_user_message(STATE_DIR / session.id)
    if last:
        click.echo("\n─── last message ───")
        click.echo(last)
