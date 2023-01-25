"""
CLI Post to Mastodon.  Source of post based off of parameters passed command.
"""
import click
import mastodon
import enum
import time

from mastodon import Mastodon
from click.core import Context
from rich.prompt import Prompt
from src import console
from src.util import filter_words, remove_word, split_string, error_info, download_image
from src.external import openai
from bs4 import BeautifulSoup


class ListenerResponseType(enum.Enum):
    REVERSE_STRING = 1
    OPEN_AI_CHAT = 2
    OPEN_AI_IMAGE = 3

class Listener(mastodon.StreamListener):
    def __init__(self, mastodon_api, openai_api_key, response_type, debugging):
        self.mastodon_api = mastodon_api
        self.openai_api_key = openai_api_key
        self.response_type = response_type
        self.debugging = debugging
        click.echo(f"{self.response_type}, Listening...")

    def on_update(self, status):
        if self.debugging:
            click.echo(f"on_update: {status}")

        convo_id = None
        image_url = None

        if "in_reply_to_id" in status and status["in_reply_to_id"] != "":
            convo_id = status["in_reply_to_id"]

        if convo_id == None and "id" in status:
            convo_id = status["id"]

        if "content" in status:
            if self.debugging:
                click.echo(f"pre BeautifulSoup content: {status['content']}")

            inner_content = BeautifulSoup(status["content"], "html.parser").text

            if "media_attachments" in status and len(status["media_attachments"]) > 0:
                image_url = status["media_attachments"][0].url

            if self.debugging:
                click.echo(f"on_update: { convo_id} \n content: {inner_content}")

            if not status["account"]["bot"]:
                self.respond(inner_content, convo_id, image_url)

    def on_notification(self, notification):
        if self.debugging:
            click.echo(f"on_notification: {notification}")

        convo_id = None
        image_url = None

        if "in_reply_to_id" in notification:
            convo_id = notification["status"]["in_reply_to_id"]

        if convo_id == None and "status" in notification:
            convo_id = notification["status"]["id"]

        if "status" in notification:
            if self.debugging:
                click.echo(
                    f"pre BeautifulSoup content: {notification['status']['content']}"
                )

            inner_content = BeautifulSoup(
                notification["status"]["content"], "html.parser"
            ).text

            if "media_attachments" in notification["status"] and len(notification["status"]["media_attachments"]) > 0:
                image_url = notification["status"]["media_attachments"][0].url

            if self.debugging:
                click.echo(f"on_notification: { convo_id} \n content: {inner_content}")

            if not notification["account"]["bot"]:
                self.respond(inner_content, convo_id, image_url)

    def on_conversation(self, conversation):
        if self.debugging:
            click.echo(f"on_conversation: {conversation}")

        convo_id = None
        image_url = None

        if "status" in conversation:
            if "in_reply_to_id" in conversation["status"]:
                convo_id = conversation["status"]["in_reply_to_id"]

            if convo_id == None:
                convo_id = conversation["status"]["id"]

            if self.debugging:
                click.echo(
                    f"pre BeautifulSoup content: {conversation['status']['content']}"
                )

            inner_content = BeautifulSoup(
                conversation["status"]["content"], "html.parser"
            ).text

            if "media_attachments" in conversation["status"] and len(conversation["status"]["media_attachments"]) > 0:
                image_url = conversation["status"]["media_attachments"][0].url

            if self.debugging:
                click.echo(f"on_conversation: { convo_id} \n content: {inner_content}")

            if not conversation["account"]["bot"]:
                self.respond(inner_content, convo_id, image_url)

    def respond(self, content, convo_id, image_url):
        words_to_filter = filter_words(content, "@")
        filtered_content = content
        response_content = None
        media_ids = []

        for word in words_to_filter:
            filtered_content = remove_word(string=filtered_content, word=word)

        if self.response_type == ListenerResponseType.REVERSE_STRING:
            response_content = filtered_content[::-1]

        if self.response_type == ListenerResponseType.OPEN_AI_CHAT:
            chat = openai.OpenAiChat(self.openai_api_key)
            chat_response = chat.create(filtered_content)
            if not chat_response:
                chat_response = "beep bop, bop beep"
            response_content = chat_response

        if self.response_type == ListenerResponseType.OPEN_AI_IMAGE:
            response_content = self.get_image_response_content(image_url, filtered_content, media_ids)

        if self.debugging:
            click.echo(f"status_post: {response_content}")

        split_response_content = split_string(response_content, 500)
        for split_content in split_response_content:
            toot = self.mastodon_api.status_post(
                split_content,
                sensitive=False,
                visibility="private",
                spoiler_text=None,
                in_reply_to_id=convo_id,
                media_ids=media_ids,
            )
            click.echo(toot["url"])
            time.sleep(1)

        if self.debugging:
            click.echo("\n")

    def get_image_response_content(self, image_url, filtered_content, media_ids):
        
        image_ai = openai.OpenAiImage(self.openai_api_key)

        if image_url:
            image_byes = download_image(self.debugging, image_url)

        if image_url and filtered_content == "variation":
            image_result = image_ai.variation(debugging=self.debugging, image=image_byes)

        elif image_url and filtered_content == "edit":
            click.echo("Not yet implemented")

        else:
            image_result = image_ai.create(filtered_content)

        image_name = filtered_content.replace(" ", "_") + ".png"
        ai_media_post = self.mastodon_api.media_post(
                media_file=image_result,
                file_name=image_name,
                mime_type="mime_type='image/png'",
            )
        media_ids.append(ai_media_post["id"])
        response_content = f"Image Generated from: {filtered_content}"
        return response_content


@click.command(
    "listen",
    short_help="Listen for all events in a blocking manner and respond based off of the paramaters you pass",
)
@click.pass_context
@click.argument("mastodon_host", required=True, type=click.STRING)
@click.argument("mastodon_client_id", required=True, type=click.STRING)
@click.argument("mastodon_client_secret", required=True, type=click.STRING)
@click.argument("mastodon_access_token", required=True, type=click.STRING)
@click.argument("openai_api_key", required=False, type=click.STRING)
@click.argument("response_type", required=False, type=click.STRING)
def listen(
    ctx,
    mastodon_host,
    mastodon_client_id,
    mastodon_client_secret,
    mastodon_access_token,
    openai_api_key,
    response_type,
):
    """
    CLI Listen to Mastodon User in a blocking manner
    """

    mastodon_api = Mastodon(
        client_id=mastodon_client_id,
        client_secret=mastodon_client_secret,
        access_token=mastodon_access_token,
        api_base_url=mastodon_host,
    )

    try:
        response_type_value = ListenerResponseType[response_type]

        mastodon_api.stream_user(
            Listener(
                mastodon_api=mastodon_api,
                openai_api_key=openai_api_key,
                response_type=response_type_value,
                debugging=ctx.obj["debugging"],
            )
        )

    except Exception as e:
        click.echo(error_info(e))