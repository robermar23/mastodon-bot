"""
CLI Post to Mastodon.  Source of post based off of parameters passed command.
"""
import click
import random
import mimetypes
import logging

from mastodon import Mastodon
from src.external import dropbox
from src.external import openai

@click.command("post", short_help="Post content to a mastodon instance")
@click.pass_context
@click.argument("mastodon_host", required=True, type=click.STRING)
@click.argument("mastodon_client_id", required=True, type=click.STRING)
@click.argument("mastodon_client_secret", required=True, type=click.STRING)
@click.argument("mastodon_access_token", required=True, default=True, type=click.STRING)
@click.argument("dropbox_client_id", required=False, type=click.STRING)
@click.argument("dropbox_client_secret", required=False, type=click.STRING)
@click.argument("dropbox_refresh_token", required=False, type=click.STRING)
@click.argument("dropbox_folder", required=False, type=click.STRING)
@click.argument("openai_api_key", required=False, type=click.STRING)
@click.argument("openai_default_completion", required=False, type=click.STRING)
def post(
    ctx,
    mastodon_host,
    mastodon_client_id,
    mastodon_client_secret,
    mastodon_access_token,
    dropbox_client_id,
    dropbox_client_secret,
    dropbox_refresh_token,
    dropbox_folder,
    openai_api_key,
    openai_default_completion,
):
    """
    CLI Post to Mastodon
    """

    result = []
    
    logging.debug(mastodon_host)
    logging.debug(mastodon_client_id)
    logging.debug(mastodon_client_secret)
    logging.debug(mastodon_access_token)
    logging.debug(dropbox_client_id)
    logging.debug(dropbox_client_secret)
    logging.debug(dropbox_refresh_token)
    logging.debug(dropbox_folder)

    mastodon_api = Mastodon(
        client_id=mastodon_client_id,
        client_secret=mastodon_client_secret,
        access_token=mastodon_access_token,
        api_base_url=mastodon_host,
    )

    if (
        dropbox_client_id
        and dropbox_client_secret
        and dropbox_refresh_token
        and dropbox_folder
    ):
        
        logging.debug("Have dropbox token, processing for dropbox source...")

        listing = dropbox.get_folder_files(
            client_id=dropbox_client_id,
            client_secret=dropbox_client_secret,
            refresh_token=dropbox_refresh_token,
            folder=dropbox_folder,
        )
        
        logging.debug(f"Found {len(listing)} files in {dropbox_folder}")

        random_file = random.choice(list(listing.keys()))

        logging.debug(f"randomly chose: {random_file}")

        file_data = dropbox.get_file_data(
            client_id=dropbox_client_id,
            client_secret=dropbox_client_secret,
            refresh_token=dropbox_refresh_token,
            folder=dropbox_folder,
            subfolder="",
            name=random_file,
        )

        mime_type = mimetypes.guess_type(random_file)
        
        logging.debug(f"guessed mime_type: {mime_type}")

        # the binary data returned from dropbox get_file_data can be passed directly to media_file parm for mastodon media_post
        media = mastodon_api.media_post(
            media_file=file_data,
            file_name=random_file,
            mime_type=f"mime_type='{mime_type}'",
        )

        status_post = "I love me!"

        if openai_api_key and openai_default_completion:
            chat = openai.OpenAiChat(openai_api_key)
            status_post = chat.create(openai_default_completion)

        toot = mastodon_api.status_post(
            status_post,
            media_ids=[media["id"]],
            sensitive=False,
            visibility="private",
            spoiler_text=None,
        )

        logging.debug(f"status_post: {status_post}")

        result.append(toot["url"])

    return result
