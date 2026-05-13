"""Interactive fzf session picker."""

from __future__ import annotations

import os
import subprocess
import sys

import click

from cockpit.store import collect_sessions, find_active_sessions


def _fzf_line(s) -> str:
    dot = "● " if s.active else "  "
    date = s.updated_at[:16].replace("T", " ") if s.updated_at else "?"
    branch = " ⑂" if s.is_branch else ""
    turns = f"[{s.turn_count}↻]"
    display = f"{dot}{date}  {turns:>6}  {s.display_name}{branch}  │  {s.display_cwd}"
    return f"{s.id}\t{s.cwd}\t{display}"


@click.command()
@click.argument("query", default="")
@click.option("-n", "--limit", default=50, help="Max sessions to show (0 = all).")
@click.option("--empty", is_flag=True, help="Include sessions with 0 turns.")
def picker_cmd(query: str, limit: int, empty: bool):
    """Interactive session picker (default command)."""
    sessions = collect_sessions(limit=limit, include_empty=empty)

    if not sessions:
        click.echo("No sessions found.", err=True)
        sys.exit(1)

    fzf_input = "\n".join(_fzf_line(s) for s in sessions)
    preview_cmd = f"python3 -m cockpit.preview {{1}}"

    try:
        result = subprocess.run(
            [
                "fzf",
                "--query", query,
                "--with-nth=3",
                "--delimiter=\t",
                "--ansi",
                "--reverse",
                "--height=~40%",
                "--no-sort",
                "--header=● = active  ⑂ = branch  [N↻] = turns  │  enter=resume  ctrl-y=copy ID",
                f"--preview={preview_cmd}",
                "--preview-window=down:4:wrap",
                "--bind=ctrl-y:execute-silent(echo -n {1} | pbcopy)+abort",
            ],
            input=fzf_input,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        click.echo("fzf is required. Install it or use 'cockpit list'.", err=True)
        sys.exit(1)

    if result.returncode != 0:
        sys.exit(0)

    selected = result.stdout.strip()
    if not selected:
        sys.exit(0)

    parts = selected.split("\t")
    sid = parts[0]
    cwd = parts[1] if len(parts) > 1 and parts[1] else os.path.expanduser("~")

    active = find_active_sessions()
    if sid in active:
        click.echo(f"Session is already active (pid {active[sid]}).")
        click.echo(f"\n    cd {cwd} && copilot --resume={sid}")
        sys.exit(1)

    click.echo(f"Resuming in {cwd} ...")
    os.chdir(cwd)
    os.execvp("copilot", ["copilot", f"--resume={sid}"])
