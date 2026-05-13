"""CLI entrypoint for cockpit."""

import click

from cockpit.commands.fork import fork_cmd
from cockpit.commands.info import info_cmd
from cockpit.commands.list import list_cmd
from cockpit.commands.picker import picker_cmd
from cockpit.commands.prune import prune_cmd
from cockpit.commands.search import search_cmd
from cockpit.commands.stats import stats_cmd


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx: click.Context):
    """Manage, search, and clean up GitHub Copilot CLI sessions."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(picker_cmd)


cli.add_command(list_cmd, "list")
cli.add_command(picker_cmd, "resume")
cli.add_command(fork_cmd, "fork")
cli.add_command(info_cmd, "info")
cli.add_command(prune_cmd, "prune")
cli.add_command(search_cmd, "search")
cli.add_command(stats_cmd, "stats")
