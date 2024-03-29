"""
This module contains the worker function that is called by the RQ worker
"""
import time
import logging
import uuid
import re
import os
from tempfile import gettempdir
import redis
from bs4 import BeautifulSoup
from rq import Queue, Retry
from mastodon import Mastodon
from mastodon.errors import MastodonAPIError
from mastodon_bot.util import filter_words, remove_word, split_string_by_words, convo_first_status_id, download_remote_file
from mastodon_bot.util import save_local_file, detect_code_in_markdown, extract_uris, open_local_file_as_bytes
from mastodon_bot.util import break_long_string_into_paragraphs, open_local_file_as_string, is_valid_uri, convert_text_to_html, process_csv_to_dict
from mastodon_bot.external import openai
from mastodon_bot.external.s3 import s3Wrapper
from mastodon_bot.external.youtube import YouTubeWrapper
from mastodon_bot.external.polly import PollyWrapper
from mastodon_bot.lib.listen.listener_config import ListenerConfig
from mastodon_bot.lib.listen.listener_response_type import ListenerResponseType
from mastodon_bot.lib.rq.polly_task_status import polly_status_job
from mastodon_bot.markdown import to_text

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def listener_respond(
    content: str, in_reply_to_id: str, image_url: str, status_id: str, config: ListenerConfig
):
    """
    Respond to a status with a response based on the config
    """
    if config is None:
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

    logging.debug("responding with %s", config.response_type)

    if config.response_type == ListenerResponseType.REVERSE_STRING:
        response_content = filtered_content[::-1]

    if config.response_type == ListenerResponseType.OPEN_AI_PROMPT:
        is_new: bool = False
        if status_id is not None and in_reply_to_id is None:
            is_new = True

        if not is_new:
            status_id = convo_first_status_id(mastodon_api, in_reply_to_id)

        if chat_context is None:
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
        if status_id is not None and in_reply_to_id is None:
            is_new = True

        if not is_new:
            status_id = convo_first_status_id(
                mastodon_api=mastodon_api, in_reply_to_id=in_reply_to_id)

        if chat_context is None:
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

            response_content += unroll_response_content(
                in_reply_to_id, status_id, config, filtered_content, response_content, False)

        elif len(response_content) > 1000:
            logging.debug(
                "Long chat response, posting link to unrolled response")
            response_content += unroll_response_content(
                in_reply_to_id, status_id, config, filtered_content, response_content, True)

    if config.response_type == ListenerResponseType.OPEN_AI_IMAGE:
        response_content = get_image_response_content(
            mastodon_api=mastodon_api,
            openai_api_key=config.openai_api_key,
            image_url=image_url,
            filtered_content=filtered_content,
            media_ids=media_ids
        )

    if config.response_type == ListenerResponseType.OPEN_AI_TRANSCRIBE:
        if in_reply_to_id is None:
            in_reply_to_id = status_id

        if image_url is not None and len(image_url) > 0:

            logging.debug("Transcribing from uploaded file: %s", image_url)
            response_content = get_transcribe_response_content(
                mastodon_api=mastodon_api,
                in_reply_to_id=in_reply_to_id,
                audio_model=config.chat_model,
                openai_api_key=config.openai_api_key,
                audio_url=image_url
            )
        else:
            logging.debug("Transcribing from posted content: %s", filtered_content)
            response_content = ""
            # attempt to get url(s) to transcribe from content of post
            uris_to_try = extract_uris(content=filtered_content)
            for uri in uris_to_try:
                try:
                    transcribed = get_transcribe_response_content(
                        mastodon_api=mastodon_api,
                        in_reply_to_id=in_reply_to_id,
                        audio_model=config.chat_model,
                        openai_api_key=config.openai_api_key,
                        audio_url=uri
                    )
                    response_content += f"{uri}: \n\n {transcribed}\n\n"
                except Exception as e:
                    logging.error("Error trying to transcribe %s: %s", uri, e)

        if len(response_content) > 1000:
            logging.debug("Response content is long, posting link to transcription file")
            response_content += unroll_response_content(
                in_reply_to_id, status_id, config, filtered_content, response_content, True)

    if config.response_type == ListenerResponseType.TEXT_TO_SPEECH:
        if in_reply_to_id is None:
            in_reply_to_id = status_id

        response_content = prepare_text_to_speech_content(
            in_reply_to_id, config, filtered_content, response_content, media_ids, mastodon_api)

    logging.debug("status_post: %s", response_content)

    # last chance to make sure we reply to correct convo
    if in_reply_to_id is None:
        in_reply_to_id = status_id

    split_response_content = split_string_by_words(response_content, 493)
    counter = 1
    total_posts = len(split_response_content)
    for split_content in split_response_content:
        if (total_posts - counter) > 0:
            split_content += f" .../{counter}"
        else:
            split_content += f" /{counter}"

        toot = mastodon_api.status_post(
            split_content,
            sensitive=False,
            visibility="private",
            spoiler_text=None,
            in_reply_to_id=in_reply_to_id,
            media_ids=media_ids,
        )
        counter += 1
        logging.debug(toot["url"])
        time.sleep(0.5)

    logging.debug("\n")
    return response_content


def prepare_text_to_speech_content(in_reply_to_id, config, filtered_content, response_content, media_ids, mastodon_api):
    """
    Prepares the content for text to speech
    """
    if response_content is None:
        response_content = ""

    uris_to_try = extract_uris(content=filtered_content)
    if (len(uris_to_try)) > 0:
        for uri in uris_to_try:
            try:
                # allow all types of content-types we can parse for text
                allow_file_types = ["text/html",
                                    "text/plain", "text/csv", "text/markdown"]
                file_bytes, file_extension = download_remote_file(
                    uri, allow_mime_types=allow_file_types)

                temp_file_path = f"{gettempdir()}/speech_{str(uuid.uuid4())}{file_extension}"
                save_local_file(content=file_bytes, filename=temp_file_path)

                if file_extension == ".txt":
                    logging.debug("Extracting content from txt file")
                    uri_content = open_local_file_as_string(temp_file_path)
                    speech_content = get_speech_response_content(mastodon_api=mastodon_api,
                                                                 media_ids=media_ids,
                                                                 config=config,
                                                                 filtered_content=uri_content,
                                                                 in_reply_to_id=in_reply_to_id,
                                                                 voice_id=config.aws_polly_voice_id)
                    response_content += f"\n\n{speech_content}\n\n"
                elif file_extension in [".html", ".htm"]:
                    logging.debug("Extracting content from html file")
                    uri_html = open_local_file_as_string(temp_file_path)
                    #wip and not ready to be used
                    #polly_prepare = PollyPrepare(html=uri_html)
                    #uri_txt = polly_prepare.parse()
                    uri_txt = BeautifulSoup(uri_html, "html.parser").text
                    speech_content = get_speech_response_content(mastodon_api=mastodon_api,
                                                                 media_ids=media_ids,
                                                                 config=config,
                                                                 filtered_content=uri_txt,
                                                                 in_reply_to_id=in_reply_to_id,
                                                                 voice_id=config.aws_polly_voice_id)
                    response_content += f"\n\n{speech_content}\n\n"

                elif file_extension == ".md":
                    logging.debug("Extracting content from markdown file")
                    uri_md = open_local_file_as_string(temp_file_path)
                    uri_txt = to_text(markdown_text=uri_md)
                    speech_content = get_speech_response_content(mastodon_api=mastodon_api,
                                                                 media_ids=media_ids,
                                                                 config=config,
                                                                 filtered_content=uri_txt,
                                                                 in_reply_to_id=in_reply_to_id,
                                                                 voice_id=config.aws_polly_voice_id)
                    response_content += f"\n\n{speech_content}\n\n"

                elif file_extension == ".csv":
                    logging.debug("Extracting content from csv file")
                    csv_data = process_csv_to_dict(temp_file_path)
                    for row in csv_data:
                        row_text_to_use = ""
                        voice_id_to_use = config.aws_polly_voice_id

                        if "content" in row:
                            row_text_to_use = row["content"]
                        elif "text" in row:
                            row_text_to_use = row["text"]
                        elif "prompt" in row:
                            row_text_to_use = row["prompt"]
                        else:
                            row_text_to_use = row[0]

                        if "voice_id" in row:
                            voice_id_to_use = row["voice_id"]
                        elif "voice" in row:
                            voice_id_to_use = row["voice"]

                        speech_content = get_speech_response_content(mastodon_api=mastodon_api,
                                                                     media_ids=media_ids,
                                                                     config=config,
                                                                     filtered_content=row_text_to_use,
                                                                     in_reply_to_id=in_reply_to_id,
                                                                     voice_id=voice_id_to_use)
                        response_content += f"\n\n{speech_content}\n\n"

            except Exception as e:
                logging.error("Error trying to transcribe %s: %s", uri, e)
    else:
        response_content = get_speech_response_content(mastodon_api=mastodon_api,
                                                       media_ids=media_ids,
                                                       config=config,
                                                       filtered_content=filtered_content,
                                                       in_reply_to_id=in_reply_to_id,
                                                       voice_id=config.aws_polly_voice_id)

    return response_content


def unroll_response_content(in_reply_to_id, status_id, config, filtered_content, response_content, split_into_paragraphs: bool = False):
    """
    Unrolls the response content and returns the url to the unrolled content
    """
    stylesheet_link = f"https://{config.mastodon_s3_bucket_name}.s3.amazonaws.com/media_attachments/style/unroll.css"

    html_full = prepare_content_for_archive(
        filtered_content=filtered_content, response_content=response_content, stylesheet_link=stylesheet_link,
        split_into_paragraphs=split_into_paragraphs)

    s3 = s3Wrapper(access_key_id=config.mastodon_s3_access_key_id,
                   access_secret_key=config.mastodon_s3_access_secret_key,
                   bucket_name=config.mastodon_s3_bucket_name,
                   prefix_path=config.mastodon_s3_bucket_prefix_path)

    s3_file_name = f"{status_id}.html"
    if in_reply_to_id:
        s3_file_name = f"{status_id}_{in_reply_to_id}.html"

    s3_url = s3.upload_string_to_s3(html_full, s3_file_name)

    logging.debug("s3_url: %s", s3_url)

    return f"\n\n  View unrolled: {s3_url}"


def prepare_content_for_archive(filtered_content, response_content, stylesheet_link, split_into_paragraphs: bool):
    """
    Prepares the content for the archive
    """
    # break up string into paragraphs first
    if split_into_paragraphs:
        paragraphs = break_long_string_into_paragraphs(
            long_string=response_content, sentences_per_paragraph=4)
        joined_paragraphs = "\n\n".join(paragraphs)

        # convert markdown/text to html
        # html_response_content = to_html(joined_paragraphs)
        html_response_content = convert_text_to_html(joined_paragraphs)
    else:
        html_response_content = convert_text_to_html(response_content)

    html_full = f'''
                <!DOCTYPE html>
                <html>
                <head>
                    <title>{filtered_content}</title>
                    <link rel="stylesheet" type="text/css" href="{stylesheet_link}" />
                </head>
                <body>
                    {html_response_content}
                </body>
                </html>
            '''

    return html_full


def get_transcribe_response_content(mastodon_api, openai_api_key, in_reply_to_id, audio_url, audio_model):
    """
    Gets the transcribe response content
    """
    transcribe_ai = openai.OpenAiTranscribe(
        openai_api_key=openai_api_key, model=audio_model)

    temp_file_path = ""

    try:
        if audio_url and len(audio_url) > 0:

            if not is_valid_uri(audio_url):
                raise Exception(
                    f"Invalid audio url provided: {audio_url}")

            mastodon_api.status_post(
                "Please wait while I transcribe your audio.  On average, this will take fifty percent of the total time of the audio posted.",
                sensitive=False,
                visibility="private",
                spoiler_text=None,
                in_reply_to_id=in_reply_to_id,
                media_ids=[],
            )

            # does audio_url contain youtube link?
            youtube_link_regex = r"https://www.youtube.com/watch\?v="
            youtube_link_match = re.search(youtube_link_regex, audio_url)
            if youtube_link_match:
                temp_file_path = f"{gettempdir()}/audio_{str(uuid.uuid4())}.mp4"
                wrapper = YouTubeWrapper()
                wrapper.download_youtube_audio(
                    url=audio_url, filename=temp_file_path)
            else:
                audio_bytes, file_extension = download_remote_file(
                    audio_url, allow_mime_types=['audio/mp3', 'audio/mpeg', 'video/mp4'])
                temp_file_path = f"{gettempdir()}/audio_{str(uuid.uuid4())}.{file_extension}"
                save_local_file(content=audio_bytes, filename=temp_file_path)
        else:
            transcribe_result = "No valid audio provided, cannot transcribe"

        transcribe_result = transcribe_ai.create(audio_file=temp_file_path)

    except Exception as e:
        logging.error("Error trying to transcribe %s: %s", audio_url, e)
        transcribe_result = f"Error trying to transcribe {audio_url}"

    finally:
        # we now need to delete the temp file path if it exists
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

    return transcribe_result


def get_image_response_content(mastodon_api, openai_api_key, image_url, filtered_content, media_ids):
    """
    Gets the image response content
    """

    image_ai = openai.OpenAiImage(openai_api_key)

    if image_url:
        image_byes, file_extension = download_remote_file(image_url)
        logging.debug("file_extension: %s", file_extension)

    if image_url and filtered_content == "variation":
        image_result = image_ai.variation(image=image_byes)

    elif image_url and filtered_content == "edit":
        logging.debug("Not yet implemented")

    else:
        image_result = image_ai.create(filtered_content)

    image_name = filtered_content.replace(" ", "_") + ".png"
    logging.debug("image_name: %s", image_name)

    ai_media_post = mastodon_api.media_post(
        media_file=image_result,
        file_name=image_name,
        mime_type="mime_type='image/png'",
    )
    media_ids.append(ai_media_post["id"])
    response_content = f"Image Generated from: {filtered_content}"
    return response_content


def get_speech_response_content(mastodon_api, media_ids, config, filtered_content, in_reply_to_id, voice_id):
    """
    Gets the speech response content
    """
    polly_wrapper = PollyWrapper(access_key_id=config.mastodon_s3_access_key_id,
                                 access_secret_key=config.mastodon_s3_access_secret_key,
                                 regionName=config.aws_polly_region_name,)

    temp_file_name = f"speech_{str(uuid.uuid4())}.mp3"
    temp_file_path = f"{gettempdir()}/{temp_file_name}"

    if voice_id is None:
        voice_id = config.aws_polly_voice_id

    speak_direct = polly_wrapper.speak(
        text=filtered_content, voice_id=voice_id, out_file=temp_file_path)
    if speak_direct is False:
        logging.debug("enqueing polly task due to large text {temp_file_name}")
        polly_task_id = polly_wrapper.start_speak(text=filtered_content, voice_id=config.aws_polly_voice_id,
                                                  output_bucket=config.mastodon_s3_bucket_name, output_key_prefix=config.mastodon_s3_bucket_prefix_path)
        logging.info("enqueuing polly status job: {polly_task_id} {in_reply_to_id}")
        redis_conn = redis.from_url(config.rq_redis_connection)
        queue = Queue(config.rq_queue_name, connection=redis_conn)
        queue.enqueue(
            polly_status_job,
            kwargs={
                'in_reply_to_id': in_reply_to_id,
                'polly_task_id': polly_task_id,
                'config': config
            },
            # we retry up to one hour for these async jobs
            retry=Retry(max=60,
                        interval=60),  # in seconds
            job_timeout=config.rq_queue_task_timeout
        )
        response_content = "AWS Polly task enqueued, please wait..."
    else:
        logging.debug("posting media to mastodon with name %s", temp_file_name)

        # attempt to post to mastodon with audio file.
        # if to large, exception will be raised and we then upload to s3 and return link
        s3_url = None
        try:
            ai_media_post = mastodon_api.media_post(
                media_file=open_local_file_as_bytes(temp_file_path),
                file_name=temp_file_name,
                mime_type="mime_type='audio/mp3'",
                synchronous=True
            )
            media_ids.append(ai_media_post["id"])
        except MastodonAPIError as e:
            logging.error("MastodonAPIError: %s", e)
            logging.info("Uploading to S3 and returning link instead")

            # also post to s3:
            s3 = s3Wrapper(access_key_id=config.mastodon_s3_access_key_id,
                           access_secret_key=config.mastodon_s3_access_secret_key,
                           bucket_name=config.mastodon_s3_bucket_name,
                           prefix_path=config.mastodon_s3_bucket_prefix_path)

            s3_key = f"{in_reply_to_id}.mp3"
            s3_url = s3.upload_file_to_s3(
                file_path=temp_file_path, s3_key=s3_key, content_type="audio/mp3")
        finally:
            # we now need to delete the temp file path if it exists
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

        if s3_url is not None:
            response_content = f"Audio Generated from: {filtered_content} \n\n  View unrolled: {s3_url}"
        else:
            response_content = f"Audio Generated from: {filtered_content}"

    return response_content
