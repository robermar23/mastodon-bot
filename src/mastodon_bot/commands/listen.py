"""
CLI Post to Mastodon.  Source of post based off of parameters passed command.
"""
import click
import mastodon
import logging
from mastodon import Mastodon
from mastodon_bot.util import error_info
from mastodon_bot.worker import listener_respond
from mastodon_bot.lib.listen.listener_config import ListenerConfig
from mastodon_bot.lib.listen.listener_response_type import ListenerResponseType
from bs4 import BeautifulSoup
from rq import Queue, Retry
from redis import Redis


class Listener(mastodon.StreamListener):
    def __init__(self, **kwargs):
        self.config = ListenerConfig(**kwargs)
        self.mastodon_api = kwargs.get("mastodon_api", None)

        logging.info(f"{self.config.response_type}, Listening...")

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

            inner_content = BeautifulSoup(
                status["content"], "html.parser").text

            if "media_attachments" in status and len(status["media_attachments"]) > 0:
                image_url = status["media_attachments"][0].url
                logging.debug(f"image_url: {image_url}")

            logging.info(
                f"on_update: { status_id}, in_reply_to_id: {in_reply_to_id} \n content: {inner_content}"
            )

            if not status["account"]["bot"]:
                self.enqueue_response(
                    status_id, in_reply_to_id, image_url, inner_content)
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
                self.enqueue_response(
                    status_id, in_reply_to_id, image_url, inner_content)
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
                self.enqueue_response(
                    status_id, in_reply_to_id, image_url, inner_content)
            else:
                logging.debug("i'm a bot, so not responding")

    def enqueue_response(self, status_id, in_reply_to_id, image_url, inner_content):
        if self.config.rq_redis_connection:
            logging.info(f"enqueuing: {status_id} {in_reply_to_id}")
            redis_conn = Redis.from_url(self.config.rq_redis_connection)
            queue = Queue(self.config.rq_queue_name, connection=redis_conn)
            queue.enqueue(
                listener_respond,
                kwargs={
                    'content': inner_content,
                    'in_reply_to_id': in_reply_to_id,
                    'image_url': image_url,
                    'status_id': status_id,
                    'config': self.config
                },
                retry=Retry(max=self.config.rq_queue_retry_attempts,
                            interval=self.config.rq_queue_retry_delay)
            )
        else:
            listener_respond(
                content=inner_content,
                in_reply_to_id=in_reply_to_id,
                image_url=image_url,
                status_id=status_id,
                config=self.config
            )


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
@click.argument("openai_chat_persona", required=False, type=click.STRING)
@click.argument("rq_redis_connection", required=False, type=click.STRING)
@click.argument("rq_queue_name", required=False, type=click.STRING)
@click.argument("rq_queue_retry_attempts", required=False, type=click.INT)
@click.argument("rq_queue_retry_delay", required=False, type=click.INT)
@click.argument("mastodon_s3_bucket_name", required=False, type=click.STRING)
@click.argument("mastodon_s3_bucket_prefix_path", required=False, type=click.STRING)
@click.argument("mastodon_s3_access_key_id", required=False, type=click.STRING)
@click.argument("mastodon_s3_access_secret_key", required=False, type=click.STRING)
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
    openai_chat_max_age_hours,
    openai_chat_persona,
    rq_redis_connection,
    rq_queue_name,
    rq_queue_retry_attempts,
    rq_queue_retry_delay,
    mastodon_s3_bucket_name,
    mastodon_s3_bucket_prefix_path,
    mastodon_s3_access_key_id,
    mastodon_s3_access_secret_key
):
    """
    CLI Listen to Mastodon User in a blocking manner
    """

    logging.debug(f"mastodon_host: {mastodon_host}")
    logging.debug(f"mastodon_client_id: {mastodon_client_id}")
    logging.debug(f"mastodon_client_secret: {mastodon_client_secret}")
    logging.debug(f"mastodon_access_token: {mastodon_access_token}")
    logging.debug(f"response_type: {response_type}")
    logging.debug(f"openai_chat_model: {openai_chat_model}")
    logging.debug(f"openai_chat_temperature: {openai_chat_temperature}")
    logging.debug(f"openai_chat_max_tokens: {openai_chat_max_tokens}")
    logging.debug(f"openai_chat_top_p: {openai_chat_top_p}")
    logging.debug(
        f"openai_chat_frequency_penalty: {openai_chat_frequency_penalty}")
    logging.debug(
        f"openai_chat_presence_penalty: {openai_chat_presence_penalty}")
    logging.debug(f"openai_chat_max_age_hours: {openai_chat_max_age_hours}")
    logging.debug(f"openai_chat_persona: {openai_chat_persona}")
    logging.debug(f"rq_redis_connection: {rq_redis_connection}")
    logging.debug(f"rq_queue_name: {rq_queue_name}")
    logging.debug(f"rq_queue_retry_attempts: {rq_queue_retry_attempts}")
    logging.debug(f"rq_queue_retry_delay: {rq_queue_retry_delay}")

    logging.debug(f"mastodon_s3_bucket_name: {mastodon_s3_bucket_name}")
    logging.debug(f"mastodon_s3_bucket_prefix_path: {mastodon_s3_bucket_prefix_path}")
    logging.debug(f"mastodon_s3_access_key_id: {mastodon_s3_access_key_id}")
    logging.debug(f"mastodon_s3_access_secret_key: {mastodon_s3_access_secret_key}")


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
                chat_max_age_hours_context=openai_chat_max_age_hours,
                chat_persona=openai_chat_persona,
                rq_redis_connection=rq_redis_connection,
                rq_queue_name=rq_queue_name,
                rq_queue_retry_attempts=rq_queue_retry_attempts,
                rq_queue_retry_delay=rq_queue_retry_delay,
                mastodon_client_id=mastodon_client_id,
                mastodon_client_secret=mastodon_client_secret,
                mastodon_access_token=mastodon_access_token,
                mastodon_host=mastodon_host,
                mastodon_s3_bucket_name=mastodon_s3_bucket_name,
                mastodon_s3_bucket_prefix_path=mastodon_s3_bucket_prefix_path,
                mastodon_s3_access_key_id=mastodon_s3_access_key_id,
                mastodon_s3_access_secret_key=mastodon_s3_access_secret_key
            )
        )

    except Exception as e:
        logging.error(error_info(e))
