"""Interactive fzf session picker."""

from __future__ import annotations

import os
import subprocess
import sys

import click

from cockpit.config import Config
from cockpit.store import collect_sessions, find_active_sessions

# ANSI color helpers
_BOLD = "\033[1m"
_DIM = "\033[2m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_CYAN = "\033[36m"
_MAGENTA = "\033[35m"
_RESET = "\033[0m"


def _fzf_line(s) -> str:
    if s.active:
        dot = f"{_GREEN}●{_RESET} "
    else:
        dot = "  "
    date = s.updated_at[:16].replace("T", " ") if s.updated_at else "?"
    branch = f" {_MAGENTA}⑂{_RESET}" if s.is_branch else ""
    turns = f"[{s.turn_count}↻]"
    name = f"{_BOLD}{s.display_name}{_RESET}" if s.turn_count > 0 else f"{_DIM}{s.display_name}{_RESET}"
    cwd = f"{_DIM}{s.display_cwd}{_RESET}"
    display = f"{dot}{_DIM}{date}{_RESET}  {_CYAN}{turns:>6}{_RESET}  {name}{branch}  │  {cwd}"
    return f"{s.id}\t{s.cwd}\t{display}"


def fzf_lines(limit: int = 50, include_empty: bool = False) -> str:
    """Generate all fzf input lines. Also used by _fzf-reload."""
    sessions = collect_sessions(limit=limit, include_empty=include_empty)
    return "\n".join(_fzf_line(s) for s in sessions)


@click.command()
@click.argument("query", default="")
@click.option("-n", "--limit", default=50, help="Max sessions to show (0 = all).")
@click.option("--empty", is_flag=True, help="Include sessions with 0 turns.")
def picker_cmd(query: str, limit: int, empty: bool):
    """Interactive session picker (default command)."""
    fzf_input = fzf_lines(limit=limit, include_empty=empty)

    if not fzf_input:
        click.echo("No sessions found.", err=True)
        sys.exit(1)

    preview_cmd = "cockpit _preview {1}"
    reload_cmd = f"cockpit _fzf-reload --limit={limit}" + (" --empty" if empty else "")
    delete_cmd = "echo {} | cut -f1 | xargs -I% sh -c 'rm -rf ~/.copilot/session-state/% && echo Deleted %'"

    try:
        result = subprocess.run(
            [
                "fzf",
                "--query",
                query,
                "--with-nth=3",
                "--delimiter=\t",
                "--ansi",
                "--reverse",
                "--height=~50%",
                "--no-sort",
                "--header=enter=resume  ctrl-y=copy ID  ctrl-d=delete  ctrl-f=fork  ctrl-r=refresh",
                f"--preview={preview_cmd}",
                "--preview-window=down:6:wrap",
                "--bind=ctrl-y:execute-silent(echo -n {1} | pbcopy)+abort",
                f"--bind=ctrl-d:execute-silent({delete_cmd})+reload({reload_cmd})",
                "--bind=ctrl-f:execute(cockpit fork {1})",
                f"--bind=ctrl-r:reload({reload_cmd})",
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

    cfg = Config.load()
    args = ["copilot", *cfg.copilot_args, f"--resume={sid}"]
    click.echo(f"Resuming in {cwd} ...")
    os.chdir(cwd)
    os.execvp("copilot", args)


@click.command(hidden=True)
@click.option("-n", "--limit", default=50)
@click.option("--empty", is_flag=True)
def fzf_reload_cmd(limit: int, empty: bool):
    """Internal: regenerate fzf lines for reload binding."""
    click.echo(fzf_lines(limit=limit, include_empty=empty))
