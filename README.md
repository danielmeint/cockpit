# cockpit

Manage, search, and clean up GitHub Copilot CLI sessions.

## Install

```bash
pip install -e ".[dev]"
```

## Usage

```bash
cockpit              # interactive fzf session picker
cockpit list         # plain-text list with turn counts
cockpit info <ID>    # detailed session view
cockpit fork [ID]    # fork/branch a session
cockpit prune        # delete empty sessions
cockpit search <Q>   # full-text search across sessions
cockpit stats        # aggregate session statistics
```

## License

MIT
