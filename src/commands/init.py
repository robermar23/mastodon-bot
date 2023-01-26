"""
CLI initialization command.
"""
import click
from rich.prompt import Prompt

from src import console
from src.constants import WELCOME_MESSAGE

@click.command()
def init():
    """
    CLI Initialization demo.
    """
    click.echo(WELCOME_MESSAGE)