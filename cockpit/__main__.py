"""Allow `python -m cockpit` to invoke the CLI."""

from cockpit.cli import cli

if __name__ == "__main__":
    cli()
