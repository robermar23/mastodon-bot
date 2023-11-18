"""
CLI initialization command.
"""
import click
from mastodon_bot.constants import WELCOME_MESSAGE

@click.command()
def init():
    """
    CLI Initialization demo.
    """
    click.echo(WELCOME_MESSAGE)