# cockpit

Manage, search, and clean up [GitHub Copilot CLI](https://github.com/features/copilot/cli) sessions.

## Prerequisites

- Python ≥ 3.11
- [fzf](https://github.com/junegunn/fzf) (for the interactive picker)

## Install

```bash
# From GitHub (recommended)
pipx install git+https://github.com/danielmeint/cockpit.git

# Or for development
git clone https://github.com/danielmeint/cockpit.git
cd cockpit
pip install -e ".[dev]"
```

## Usage

```bash
cockpit                  # interactive fzf picker (default)
cockpit list             # plain-text list with turn counts
cockpit list --size      # include disk usage per session
cockpit info <ID>        # detailed session view
cockpit fork [ID]        # fork/branch a session
cockpit fork -n 5        # fork, keeping only last 5 turns
cockpit prune            # delete empty sessions (interactive)
cockpit prune --dry-run  # show what would be deleted
cockpit search <QUERY>   # full-text search across sessions
cockpit stats            # aggregate statistics
```

## Picker keybindings

| Key      | Action                        |
|----------|-------------------------------|
| `enter`  | Resume selected session       |
| `ctrl-y` | Copy session ID to clipboard  |
| `ctrl-d` | Delete session + refresh list |
| `ctrl-f` | Fork session                  |
| `ctrl-r` | Refresh list                  |

## Configuration

Optional config file at `~/.config/cockpit/config.toml`:

```toml
# Extra arguments passed to `copilot` when resuming a session
copilot_args = ["--yolo"]
```

## Example output

```
$ cockpit list -n 5
● 2026-05-13 06:32    [5↻]  Refactor Auth Module  │  ~/projects/myapp
● 2026-05-13 06:30   [20↻]  Debug Flaky Tests  │  ~/projects/myapp
  2026-05-12 15:22   [14↻]  Plan API Redesign  │  ~/projects/api
  2026-05-12 14:31   [35↻]  Migrate Database Schema  │  ~/projects/api
  2026-05-12 09:02   [18↻]  Review PR #42  │  ~/projects/myapp

$ cockpit stats
═══ Cockpit Stats ═══

Sessions:     410
  Active:     2
  Empty:      154 (62K)
  Branches:   1
Total turns:  2530
Disk usage:   444.0M
```

## License

[MIT](LICENSE)

