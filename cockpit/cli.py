"""CLI entrypoint for cockpit."""

import click

from cockpit.commands.list import list_cmd
from cockpit.commands.picker import picker_cmd


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx: click.Context):
    """Manage, search, and clean up GitHub Copilot CLI sessions."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(picker_cmd)


cli.add_command(list_cmd, "list")
cli.add_command(picker_cmd, "resume")
