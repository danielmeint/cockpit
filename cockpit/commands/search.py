"""Full-text search across session content."""

from __future__ import annotations

import json
import re

import click

from cockpit.store import STATE_DIR, collect_sessions


def _search_session(session_id: str, pattern: re.Pattern, max_snippets: int = 3) -> list[str]:
    """Search events.jsonl for matching user/assistant messages. Returns context snippets."""
    events_path = STATE_DIR / session_id / "events.jsonl"
    if not events_path.exists():
        return []

    snippets: list[str] = []
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
                    role = "user"
                elif etype == "assistant.message":
                    content = evt.get("data", {}).get("content", "")
                    role = "assistant"
                else:
                    continue

                if not content or not pattern.search(content):
                    continue

                # Extract snippet around match
                match = pattern.search(content)
                start = max(0, match.start() - 60)
                end = min(len(content), match.end() + 60)
                snippet = content[start:end].replace("\n", " ").strip()
                if start > 0:
                    snippet = "…" + snippet
                if end < len(content):
                    snippet = snippet + "…"
                snippets.append(f"  [{role}] {snippet}")

                if len(snippets) >= max_snippets:
                    break
    except OSError:
        pass
    return snippets


@click.command()
@click.argument("query")
@click.option("-n", "--limit", default=0, help="Max sessions to search (0 = all).")
@click.option("--repo", default=None, help="Filter by repository name.")
@click.option("--cwd", default=None, help="Filter by working directory (substring).")
@click.option("-i", "--ignore-case", is_flag=True, help="Case-insensitive search.")
def search_cmd(query: str, limit: int, repo: str | None, cwd: str | None, ignore_case: bool):
    """Search across all session conversations."""
    flags = re.IGNORECASE if ignore_case else 0
    try:
        pattern = re.compile(re.escape(query), flags)
    except re.error as e:
        click.echo(f"Invalid search pattern: {e}", err=True)
        raise SystemExit(1) from e

    sessions = collect_sessions(limit=limit, include_empty=False)

    if repo:
        sessions = [s for s in sessions if repo.lower() in (s.repository or "").lower()]
    if cwd:
        sessions = [s for s in sessions if cwd in s.cwd]

    found = 0
    for s in sessions:
        snippets = _search_session(s.id, pattern)
        if not snippets:
            continue
        found += 1
        date = s.updated_at[:16].replace("T", " ") if s.updated_at else "?"
        click.echo(f"\n● {date}  [{s.turn_count}↻]  {s.display_name}  │  {s.display_cwd}")
        click.echo(f"  id: {s.id}")
        for snippet in snippets:
            click.echo(snippet)

    if found == 0:
        click.echo(f'No matches for "{query}".')
    else:
        click.echo(f"\n{found} session(s) matched.")
