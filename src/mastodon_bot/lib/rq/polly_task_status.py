import logging
from mastodon import Mastodon
from mastodon.errors import MastodonAPIError
from mastodon_bot.lib.listen.listener_config import ListenerConfig
from mastodon_bot.external.s3 import s3Wrapper

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def polly_status_job(in_reply_to_id: str, polly_task_id: str, config: ListenerConfig):
    if config == None:
        raise ValueError("ListenerConfig cannot be None")

    logging.getLogger().setLevel(logging.DEBUG)

    # we do not want to catch exceptions here, as the rq job retry will retry if we let exceptions bubble up
    # in this case, if the s3 file does not exist when we ask for it, we want to let the 404 exception bubble up
    # so rq can retry

    wrapper = s3Wrapper(access_key_id=config.mastodon_s3_access_key_id,
                        access_secret_key=config.mastodon_s3_access_secret_key, bucket_name=config.mastodon_s3_bucket_name,
                        prefix_path=config.mastodon_s3_bucket_prefix_path)

    task_s3_key = f".{polly_task_id}.mp3"
    try_file = wrapper.get_file(task_s3_key)

    if try_file == None:
        raise Exception(f"S3 file {task_s3_key} not found yet")

    s3_url = None
    media_post_ids = []

    try:
        mastodon_api = Mastodon(
            client_id=config.mastodon_client_id,
            client_secret=config.mastodon_client_secret,
            access_token=config.mastodon_access_token,
            api_base_url=config.mastodon_host,
        )

        ai_media_post = mastodon_api.media_post(
            media_file=try_file,
            file_name=task_s3_key,
            mime_type="mime_type='audio/mp3'",
            synchronous=True
        )

        media_post_ids.append(ai_media_post["id"])

    except MastodonAPIError as e:
        logging.error(f"Exception: {e}")
        logging.info(f"Returning existing link to S3 instead")

        s3_url = s3Wrapper.get_public_url(task_s3_key)

    if s3_url is not None:
        response_content = f"Audio Stored in S3: {s3_url}"
    else:
        response_content = f"Audio attached"

    mastodon_api.status_post(
        response_content,
        sensitive=False,
        visibility="private",
        spoiler_text=None,
        in_reply_to_id=in_reply_to_id,
        media_ids=media_post_ids,
    )
