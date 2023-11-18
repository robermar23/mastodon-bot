"""
CLI get command.
"""

import json
import click
from mastodon_bot.external.polly import PollyWrapper


@click.command("get",
               short_help="Get mastodon related stuff",)
@click.argument("data_type", required=True, type=click.STRING)
@click.option("--awsprofile", "-p", help="The AWS profile to use")
def get(data_type, awsprofile):
    """
    CLI get command to retrieve data
    """
    if data_type == "voices":
        wrapper = PollyWrapper(access_key_id="", access_secret_key="", profile_name=awsprofile)
        result = wrapper.get_voices()
        click.echo(json.dumps(result))
