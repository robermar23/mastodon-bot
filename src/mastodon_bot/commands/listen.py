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
                            interval=self.config.rq_queue_retry_delay),
                job_timeout=self.config.rq_queue_task_timeout
                
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
@click.option("--mastodon_host", help="The fqdn of the mastodon host to connect to", type=click.STRING)
@click.option("--mastodon_client_id", help="The oauth client id to use to auth as a specific mastodon user", type=click.STRING)
@click.option("--mastodon_client_secret", help="The oauth client secret to use to auth as a specific mastodon user", type=click.STRING)
@click.option("--mastodon_access_token", help="The oauth access token to use to auth as a specific mastodon user", type=click.STRING)
@click.option("--openai_api_key", help="The openai api key to use to generate responses. Otherwise, the OPENAI_API_KEY env var will be used", type=click.STRING)
@click.option("--openai_chat_model", help="The openai chat model to use. see: https://platform.openai.com/docs/models", type=click.STRING)
@click.option("--openai_chat_temperature", help="What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic", type=click.FLOAT)
@click.option("--openai_chat_max_tokens", help="The maximum number of tokens to generate in the chat completion. The total length of input tokens and generated tokens is limited by the model's context length", type=click.INT)
@click.option("--openai_chat_top_p", help="An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top_p probability mass. So 0.1 means only the tokens comprising the top 10% probability mass are considered", type=click.FLOAT)
@click.option("--openai_chat_frequency_penalty", help="Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim.", type=click.FLOAT)
@click.option("--openai_chat_presence_penalty", help="Number between -2.0 and 2.0. Positive values penalize new tokens based on whether they appear in the text so far, increasing the model's likelihood to talk about new topics.", type=click.FLOAT)
@click.option("--openai_chat_max_age_hours", help="The number of hours to keep previous conversation convesations for chat context", type=click.INT)
@click.option("--openai_chat_persona", help="The persona that chatbot should take on when responding to questions", type=click.STRING)
@click.option("--rq_redis_connection", help="The redis connection string to use for the redis queue", type=click.STRING)
@click.option("--rq_queue_name", help="The redis queue name to use for redis queue", type=click.STRING)
@click.option("--rq_queue_retry_attempts", help="The number of times to retry a failed redis queue task", type=click.INT)
@click.option("--rq_queue_retry_delay", help="The number of seconds to wait between retry attempts of a failed redis queue task", type=click.INT)
@click.option("--rq_queue_task_timeout", help="How long to wait for a redis queue task to complete before giving up", type=click.INT)
@click.option("--mastodon_s3_bucket_name", help="The s3 bucket name to use for storing conversation files", type=click.STRING)
@click.option("--mastodon_s3_bucket_prefix_path", help="The s3 bucket prefix path to use for storing conversation files", type=click.STRING)
@click.option("--mastodon_s3_access_key_id", help="The aws iam user access key id to use for s3", type=click.STRING)
@click.option("--mastodon_s3_access_secret_key", help="The aws iam user access secret key to use for s3", type=click.STRING)
@click.option("--aws_polly_region_name", help="The aws polly region name to use for text to speech", type=click.STRING)
@click.option("--aws_polly_voice_id", help="The aws polly voice id to use for text to speech", type=click.STRING)
@click.option("--postgres_host", help="The postgres host to use for embedding data retrieveal", type=click.STRING)
@click.option("--postgres_port", help="The postgres port to use for embedding data retrieveal", type=click.INT)
@click.option("--postgres_user", help="The postgres user to use for embedding data retrieveal", type=click.STRING)
@click.option("--postgres_pass_env_var", help="The environment variable to use for the postgres password to use for embedding data retrieveal", type=click.STRING)
@click.option("--postgres_database", help="The postgres database to use for embedding data retrieveal", type=click.STRING)
@click.option("--embedding_space_name", help="The name of the space to use when filtering embeddings for this bot", type=click.STRING)
@click.option("--embedding_intro_content", help="The introduction content to use when filtering embeddings for this bot", type=click.STRING)
@click.option("--embedding_model", help="The embedding model to use when making openai embedding calls", type=click.STRING)
@click.option("--embedding_token_budget", help="The token budget to use when making openai embedding calls", type=click.INT)
@click.option("--embedding_match_threshold", help="The match threshold to use when filtering embeddings for this bot", type=click.FLOAT)
@click.option("--embedding_max_count", help="The max number of results to return when filtering embeddings for this bot", type=click.INT)
@click.argument("response_type", required=False, type=click.STRING)
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
    rq_queue_task_timeout,
    mastodon_s3_bucket_name,
    mastodon_s3_bucket_prefix_path,
    mastodon_s3_access_key_id,
    mastodon_s3_access_secret_key,
    aws_polly_region_name,
    aws_polly_voice_id,
    postgres_host,
    postgres_port,
    postgres_user,
    postgres_pass_env_var,
    postgres_database,
    embedding_space_name,
    embedding_intro_content,
    embedding_model,
    embedding_token_budget,
    embedding_match_threshold,
    embedding_match_count
):
    """
    Listen to Mastodon User streaming events and act

    RESPONSE_TYPE: REVERSE_STRING, OPEN_AI_CHAT, OPEN_AI_IMAGE, OPEN_AI_PROMPT, OPEN_AI_TRANSCRIBE, TEXT_TO_SPEECH

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
    logging.debug(f"rq_queue_task_timeout: {rq_queue_task_timeout}")
    logging.debug(f"mastodon_s3_bucket_name: {mastodon_s3_bucket_name}")
    logging.debug(f"mastodon_s3_bucket_prefix_path: {mastodon_s3_bucket_prefix_path}")
    logging.debug(f"mastodon_s3_access_key_id: {mastodon_s3_access_key_id}")
    logging.debug(f"mastodon_s3_access_secret_key: {mastodon_s3_access_secret_key}")
    logging.debug(f"aws_polly_region_name: {aws_polly_region_name}")
    logging.debug(f"aws_polly_voice_id: {aws_polly_voice_id}")
    logging.debug(f"postgres_host: {postgres_host}")
    logging.debug(f"postgres_port: {postgres_port}")
    logging.debug(f"postgres_user: {postgres_user}")
    logging.debug(f"postgres_pass_env_var: {postgres_pass_env_var}")
    logging.debug(f"postgres_database: {postgres_database}")
    logging.debug(f"embedding_space_name: {embedding_space_name}")
    logging.debug(f"embedding_intro_content: {embedding_intro_content}")
    logging.debug(f"embedding_model: {embedding_model}")
    logging.debug(f"embedding_token_budget: {embedding_token_budget}")
    logging.debug(f"embedding_match_threshold: {embedding_match_threshold}")
    logging.debug(f"embedding_match_count: {embedding_match_count}")

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
                rq_queue_task_timeout=rq_queue_task_timeout,
                mastodon_client_id=mastodon_client_id,
                mastodon_client_secret=mastodon_client_secret,
                mastodon_access_token=mastodon_access_token,
                mastodon_host=mastodon_host,
                mastodon_s3_bucket_name=mastodon_s3_bucket_name,
                mastodon_s3_bucket_prefix_path=mastodon_s3_bucket_prefix_path,
                mastodon_s3_access_key_id=mastodon_s3_access_key_id,
                mastodon_s3_access_secret_key=mastodon_s3_access_secret_key,
                aws_polly_region_name=aws_polly_region_name,
                aws_polly_voice_id=aws_polly_voice_id
            )
        )

    except Exception as e:
        logging.error(error_info(e))
