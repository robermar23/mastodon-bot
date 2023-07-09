
import time
import logging
from mastodon import Mastodon
from mastodon_bot.util import filter_words, remove_word, split_string_by_words, convo_first_status_id, download_remote_file, detect_code_in_markdown
from mastodon_bot.external import openai
from mastodon_bot.external.s3 import s3Wrapper
from mastodon_bot.lib.listen.listener_config import ListenerConfig
from mastodon_bot.lib.listen.listener_response_type import ListenerResponseType
from mastodon_bot.markdown import to_html

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


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

        if detect_code_in_markdown(response_content):
            logging.debug(
                "Detected code in chat response, posting link to code file")

            stylesheet_link = f"https://{config.mastodon_s3_bucket_name}.s3.amazonaws.com/media_attachments/style/unroll.css"
            html_full = prepare_content_for_archive(
                filtered_content=filtered_content, response_content=response_content, stylesheet_link=stylesheet_link)

            s3 = s3Wrapper(access_key_id=config.mastodon_s3_access_key_id,
                           access_secret_key=config.mastodon_s3_access_secret_key,
                           bucket_name=config.mastodon_s3_bucket_name,
                           prefix_path=config.mastodon_s3_bucket_prefix_path)

            s3_file_name = f"{status_id}.html"
            if in_reply_to_id:
                s3_file_name = f"{status_id}_{in_reply_to_id}.html"

            s3_url = s3.upload_string_to_s3(html_full, s3_file_name)

            logging.debug(f"prefixing response with unrolled file {s3_url}")

            response_content += f"\n\n  View Unrolled: {s3_url}"

    if config.response_type == ListenerResponseType.OPEN_AI_IMAGE:
        response_content = get_image_response_content(
            mastodon_api=mastodon_api,
            openai_api_key=config.openai_api_key,
            image_url=image_url,
            filtered_content=filtered_content,
            media_ids=media_ids
        )

    if config.response_type == ListenerResponseType.OPEN_AI_TRANSCRIBE:
        response_content = get_transcribe_response_content(
            openai_api_key=config.openai_api_key,
            audio_url=image_url,
        )

    logging.debug(f"status_post: {response_content}")

    if in_reply_to_id == None:
        in_reply_to_id = status_id

    split_response_content = split_string_by_words(response_content, 500)
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


def prepare_content_for_archive(filtered_content, response_content, stylesheet_link):
    html_response_content = to_html(response_content)

    html_full = f'''
                <!DOCTYPE html>
                <html>
                <head>
                    <title>{filtered_content}</title>
                    <link rel="stylesheet" type="text/css" href="{stylesheet_link}" />
                </head>
                <body>
                    <p><strong{filtered_content}</strong></p>
                    {html_response_content}
                </body>
                </html>
            '''

    return html_full


def get_transcribe_response_content(openai_api_key, audio_url):

    transcribe_ai = openai.OpenAiTranscribe(openai_api_key=openai_api_key)

    if audio_url:
        audio_bytes = download_remote_file(audio_url)
    else:
        return "No audio provided, cannot transcribe"

    transcribe_result = transcribe_ai.create(audio_file=audio_bytes)

    return transcribe_result

def get_image_response_content(mastodon_api, openai_api_key, image_url, filtered_content, media_ids):

    image_ai = openai.OpenAiImage(openai_api_key)

    if image_url:
        image_byes = download_remote_file(image_url)

    if image_url and filtered_content == "variation":
        image_result = image_ai.variation(image=image_byes)

    elif image_url and filtered_content == "edit":
        logging.debug("Not yet implemented")

    else:
        image_result = image_ai.create(filtered_content)

    image_name = filtered_content.replace(" ", "_") + ".png"
    logging.debug(f"posting media to mastoton with name {image_name}")

    ai_media_post = mastodon_api.media_post(
        media_file=image_result,
        file_name=image_name,
        mime_type="mime_type='image/png'",
    )
    media_ids.append(ai_media_post["id"])
    response_content = f"Image Generated from: {filtered_content}"
    return response_content
