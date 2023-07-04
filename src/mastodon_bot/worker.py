
import time
import logging
from mastodon import Mastodon
from mastodon_bot.util import filter_words, remove_word, split_string, convo_first_status_id, get_image_response_content
from mastodon_bot.external import openai
from mastodon_bot.commands._listen.listener_config import ListenerConfig
from mastodon_bot.commands._listen.listener_response_type import ListenerResponseType

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def listener_respond(
    content: str, in_reply_to_id: str, image_url: str, status_id: str, config: ListenerConfig
):
    if config == None:
        raise ValueError("ListenerConfig cannot be None")

    logging.getLogger().setLevel(logging.DEBUG)

    words_to_filter = filter_words(content, "@")
    filtered_content = content
    response_content = None
    media_ids = []
    chat_context = None

    mastodon_api = Mastodon(
        client_id=config.mastodon_client_id,
        client_secret=config.mastodon_client_secret,
        access_token=config.mastodon_access_token,
        api_base_url=config.mastodon_host,
    )

    for word in words_to_filter:
        filtered_content = remove_word(string=filtered_content, word=word)

    logging.debug(f"responding with {config.response_type}")

    if config.response_type == ListenerResponseType.REVERSE_STRING:
        response_content = filtered_content[::-1]

    if config.response_type == ListenerResponseType.OPEN_AI_PROMPT:
        is_new: bool = False
        if status_id != None and in_reply_to_id == None:
            is_new = True

        if not is_new:
            status_id = convo_first_status_id(mastodon_api, in_reply_to_id)

        if chat_context == None:
            chat_context = openai.OpenAiPrompt(
                openai_api_key=config.openai_api_key,
                model=config.chat_model,
                temperature=config.chat_temperature,
                max_tokens=config.chat_max_tokens,
                top_p=config.chat_top_p,
                frequency_penalty=config.chat_frequency_penalty,
                presence_penalty=config.chat_presence_penalty,
                max_age_hours=config.chat_max_age_hours_context,
            )

        chat_response = chat_context.create(
            convo_id=str(status_id), prompt=filtered_content, keep_context=True
        )

        if not chat_response:
            chat_response = "beep bop, bop beep"
        response_content = chat_response

    if config.response_type == ListenerResponseType.OPEN_AI_CHAT:
        is_new: bool = False
        if status_id != None and in_reply_to_id == None:
            is_new = True

        if not is_new:
            status_id = convo_first_status_id(
                mastodon_api=mastodon_api, in_reply_to_id=in_reply_to_id)

        if chat_context == None:
            chat_context = openai.OpenAiChat(
                openai_api_key=config.openai_api_key,
                model=config.chat_model,
                temperature=config.chat_temperature,
                max_tokens=config.chat_max_tokens,
                max_age_hours=config.chat_max_age_hours_context,
                persona=config.chat_persona,
                redis_connection=config.rq_redis_connection,
            )
        response_content = chat_context.create(
            convo_id=str(status_id), prompt=filtered_content
        )

    if config.response_type == ListenerResponseType.OPEN_AI_IMAGE:
        response_content = get_image_response_content(
            image_url, filtered_content, media_ids
        )

    logging.debug(f"status_post: {response_content}")

    if in_reply_to_id == None:
        in_reply_to_id = status_id

    split_response_content = split_string(response_content, 499)
    for split_content in split_response_content:
        toot = mastodon_api.status_post(
            split_content,
            sensitive=False,
            visibility="private",
            spoiler_text=None,
            in_reply_to_id=in_reply_to_id,
            media_ids=media_ids,
        )
        logging.debug(toot["url"])
        time.sleep(0.5)

    logging.debug("\n")
    return response_content