"""
CLI get command.
"""
import click
from mastodon_bot.external.polly import PollyWrapper


@click.command("get",
               short_help="Get mastodon related stuff",)
@click.argument("data_type", required=True, type=click.STRING)
def get(data_type):
    """
    CLI get command to retrieve data
    """
    if data_type == "voices":
        wrapper = PollyWrapper()
        result = wrapper.get_voices()
        return result
