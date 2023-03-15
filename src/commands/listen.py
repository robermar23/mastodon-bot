"""
CLI Post to Mastodon.  Source of post based off of parameters passed command.
"""
import click
import mastodon
import enum
import time
import logging

from mastodon import Mastodon
from src.util import filter_words, remove_word, split_string, error_info, download_image
from src.external import openai
from bs4 import BeautifulSoup


class ListenerResponseType(enum.Enum):
    REVERSE_STRING = 1
    OPEN_AI_CHAT = 2
    OPEN_AI_IMAGE = 3


class Listener(mastodon.StreamListener):
    def __init__(self, **kwargs):
        self.mastodon_api = kwargs.get("mastodon_api", None)
        self.openai_api_key = kwargs.get("openai_api_key", None)
        self.response_type = kwargs.get("response_type", None)

        self.chat_model = kwargs.get("chat_model", None)
        self.chat_temperature = kwargs.get("chat_temperature", None)
        self.chat_max_tokens = kwargs.get("chat_max_tokens", None)
        self.chat_top_p = kwargs.get("chat_top_p", None)
        self.chat_frequency_penalty = kwargs.get("chat_frequency_penalty", None)
        self.chat_presence_penalty = kwargs.get("chat_presence_penalty", None)
        self.chat_max_age_hours_context = kwargs.get("chat_max_age_hours_context", None)
        self.chat_context = None

        logging.info(f"{self.response_type}, Listening...")

    def on_update(self, status):

        logging.debug(f"on_update: {status}")

        status_id = None
        in_reply_to_id = None
        image_url = None

        if "in_reply_to_id" in status and status["in_reply_to_id"] != "":
            in_reply_to_id = status["in_reply_to_id"]

        if "id" in status:
            status_id = status["id"]

        if "content" in status:

            logging.debug(f"pre BeautifulSoup content: {status['content']}")

            inner_content = BeautifulSoup(status["content"], "html.parser").text

            if "media_attachments" in status and len(status["media_attachments"]) > 0:
                image_url = status["media_attachments"][0].url
                logging.debug(f"image_url: {image_url}")

            logging.info(
                f"on_update: { status_id}, in_reply_to_id: {in_reply_to_id} \n content: {inner_content}"
            )

            if not status["account"]["bot"]:
                self.respond(
                    content=inner_content,
                    in_reply_to_id=in_reply_to_id,
                    image_url=image_url,
                    status_id=status_id,
                )
            else:
                logging.debug("i'm a bot, so not responding")

    def on_notification(self, notification):

        logging.debug(f"on_notification: {notification}")

        status_id = None
        in_reply_to_id = None
        image_url = None

        if (
            "status" in notification
            and "in_reply_to_id" in notification["status"]
            and notification["status"]["in_reply_to_id"] != ""
        ):
            in_reply_to_id = notification["status"]["in_reply_to_id"]

        if "status" in notification:
            status_id = notification["status"]["id"]

        if "status" in notification:
            logging.debug(
                f"pre BeautifulSoup content: {notification['status']['content']}"
            )

            inner_content = BeautifulSoup(
                notification["status"]["content"], "html.parser"
            ).text

            if (
                "media_attachments" in notification["status"]
                and len(notification["status"]["media_attachments"]) > 0
            ):
                image_url = notification["status"]["media_attachments"][0].url
                logging.debug(f"image_url: {image_url}")

            logging.info(
                f"on_notification: { status_id}, in_reply_to_id: {in_reply_to_id} \n content: {inner_content}"
            )

            if not notification["account"]["bot"]:
                self.respond(
                    content=inner_content,
                    in_reply_to_id=in_reply_to_id,
                    image_url=image_url,
                    status_id=status_id,
                )
            else:
                logging.debug("i'm a bot, so not responding")

    def on_conversation(self, conversation):

        logging.debug(f"on_conversation: {conversation}")

        status_id = None
        in_reply_to_id = None
        image_url = None

        if "status" in conversation:
            if "in_reply_to_id" in conversation["status"]:
                in_reply_to_id = conversation["status"]["in_reply_to_id"]

            status_id = conversation["status"]["id"]

            logging.debug(
                f"pre BeautifulSoup content: {conversation['status']['content']}"
            )

            inner_content = BeautifulSoup(
                conversation["status"]["content"], "html.parser"
            ).text

            if (
                "media_attachments" in conversation["status"]
                and len(conversation["status"]["media_attachments"]) > 0
            ):
                image_url = conversation["status"]["media_attachments"][0].url
                logging.debug(f"image_url: {image_url}")

            logging.info(
                f"on_conversation: { status_id}, in_reply_to_id: {in_reply_to_id} \n content: {inner_content}"
            )

            if not conversation["account"]["bot"]:
                self.respond(
                    content=inner_content,
                    in_reply_to_id=in_reply_to_id,
                    image_url=image_url,
                    status_id=status_id,
                )
            else:
                logging.debug("i'm a bot, so not responding")

    def respond(
        self, content: str, in_reply_to_id: str, image_url: str, status_id: str
    ):
        words_to_filter = filter_words(content, "@")
        filtered_content = content
        response_content = None
        media_ids = []

        for word in words_to_filter:
            filtered_content = remove_word(string=filtered_content, word=word)

        logging.debug(f"responding with {self.response_type}")

        if self.response_type == ListenerResponseType.REVERSE_STRING:
            response_content = filtered_content[::-1]

        if self.response_type == ListenerResponseType.OPEN_AI_CHAT:
            is_new: bool = False
            if status_id != None and in_reply_to_id == None:
                is_new = True

            if not is_new:
                status_id = self.convo_first_status_id(in_reply_to_id)

            if self.chat_context == None:
                self.chat_context = openai.OpenAiChat(
                    openai_api_key=self.openai_api_key,
                    model=self.chat_model,
                    temperature=self.chat_temperature,
                    max_tokens=self.chat_max_tokens,
                    top_p=self.chat_top_p,
                    frequency_penalty=self.chat_frequency_penalty,
                    presence_penalty=self.chat_presence_penalty,
                    max_age_hours=self.chat_max_age_hours,
                )

            chat_response = self.chat_context.create(
                convo_id=str(status_id), prompt=filtered_content, keep_context=True
            )

            if not chat_response:
                chat_response = "beep bop, bop beep"
            response_content = chat_response

        if self.response_type == ListenerResponseType.OPEN_AI_IMAGE:
            response_content = self.get_image_response_content(
                image_url, filtered_content, media_ids
            )

        logging.debug(f"status_post: {response_content}")

        if in_reply_to_id == None:
            in_reply_to_id = status_id

        split_response_content = split_string(response_content, 500)
        for split_content in split_response_content:
            toot = self.mastodon_api.status_post(
                split_content,
                sensitive=False,
                visibility="private",
                spoiler_text=None,
                in_reply_to_id=in_reply_to_id,
                media_ids=media_ids,
            )
            logging.debug(toot["url"])
            time.sleep(1)

        logging.debug("\n")

    def convo_first_status_id(self, in_reply_to_id):
        first_status = False
        last_status_id = in_reply_to_id
        while not first_status:
            last_status = self.mastodon_api.status(last_status_id)
            last_status_in_reply_to_id = last_status["in_reply_to_id"]
            if last_status_in_reply_to_id == None:
                first_status = True
            else:
                last_status_id = last_status_in_reply_to_id

        status_id = last_status_id
        return status_id

    def get_image_response_content(self, image_url, filtered_content, media_ids):

        image_ai = openai.OpenAiImage(self.openai_api_key)

        if image_url:
            image_byes = download_image(image_url)

        if image_url and filtered_content == "variation":
            image_result = image_ai.variation(image=image_byes)

        elif image_url and filtered_content == "edit":
            logging.debug("Not yet implemented")

        else:
            image_result = image_ai.create(filtered_content)

        image_name = filtered_content.replace(" ", "_") + ".png"
        logging.debug(f"posting media to mastoton with name {image_name}")

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
@click.argument("openai_chat_model", required=False, type=click.STRING)
@click.argument("openai_chat_temperature", required=False, type=click.FLOAT)
@click.argument("openai_chat_max_tokens", required=False, type=click.INT)
@click.argument("openai_chat_top_p", required=False, type=click.FLOAT)
@click.argument("openai_chat_frequency_penalty", required=False, type=click.FLOAT)
@click.argument("openai_chat_presence_penalty", required=False, type=click.FLOAT)
@click.argument("openai_chat_max_age_hours", required=False, type=click.INT)
def listen(
    ctx,
    mastodon_host,
    mastodon_client_id,
    mastodon_client_secret,
    mastodon_access_token,
    openai_api_key,
    response_type,
    openai_chat_model,
    openai_chat_temperature,
    openai_chat_max_tokens,
    openai_chat_top_p,
    openai_chat_frequency_penalty,
    openai_chat_presence_penalty,
    openai_chat_max_age_hours
):
    """
    CLI Listen to Mastodon User in a blocking manner
    """

    logging.debug(mastodon_host)
    logging.debug(mastodon_client_id)
    logging.debug(mastodon_client_secret)
    logging.debug(mastodon_access_token)
    logging.debug(response_type)
    logging.debug(openai_chat_model)
    logging.debug(openai_chat_temperature)
    logging.debug(openai_chat_max_tokens)
    logging.debug(openai_chat_top_p)
    logging.debug(openai_chat_frequency_penalty)
    logging.debug(openai_chat_presence_penalty)
    logging.debug(openai_chat_max_age_hours)

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
                chat_model=openai_chat_model,
                chat_temperature=openai_chat_temperature,
                chat_max_tokens=openai_chat_max_tokens,
                chat_top_p=openai_chat_top_p,
                chat_frequency_penalty=openai_chat_frequency_penalty,
                chat_presence_penalty=openai_chat_presence_penalty,
                chat_max_age_hours=openai_chat_max_age_hours
            )
        )

    except Exception as e:
        logging.error(error_info(e))
