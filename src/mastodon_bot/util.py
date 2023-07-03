import time
import os
import sys
import requests
import logging
import base64
from mastodon_bot.external import openai


def stopwatch(message: str):
    """Context manager to print how long a block of code took."""
    t0 = time.time()
    try:
        yield
    finally:
        t1 = time.time()
        logging.debug("Total elapsed time for %s: %.3f" % (message, t1 - t0))


# example usage
# my_string = "Hello, world! How are you doing today?"
# filtered_string = filter_words(my_string, 'H')
# print(filtered_string)
def filter_words(string, starting_char):
    # split the string into a list of words
    words = string.split()

    # create a list to store the filtered words
    filtered_words = []

    # iterate through the words
    for word in words:
        # if the word starts with the given character, add it to the filtered words list
        if word[0] == starting_char:
            filtered_words.append(word)

    # return list of filtered words
    return filtered_words


# example usage
# my_string = "This is a long string that needs to be split into smaller strings for every 500 characters."
# split_strings = split_string(my_string, 500)
# print(split_strings)
def split_string(string, max_length):
    # create an empty list to store the split strings
    split_strings = []

    # create a start index
    start_index = 0

    # while the start index is less than the length of the string
    while start_index < len(string):
        # get the end index for the current split string
        end_index = start_index + max_length

        # if the end index is greater than the length of the string, set it to the length of the string
        if end_index > len(string):
            end_index = len(string)

        # add the split string to the list
        split_strings.append(string[start_index:end_index])

        # set the start index to the end index
        start_index = end_index

    # return the list of split strings
    return split_strings


# example usage
# my_string = "This is a string with a word that needs to be removed."
# filtered_string = remove_word(my_string, "a")
# print(filtered_string)
def remove_word(string, word):
    # split the string into a list of words
    words = string.split()

    # create a list to store the filtered words
    filtered_words = []

    # iterate through the words
    for w in words:
        # if the word is not the one to remove, add it to the filtered words list
        if w != word:
            filtered_words.append(w)

    # join the filtered words list and return it
    return " ".join(filtered_words)


def error_info(e):
    """
    https://stackoverflow.com/a/1278740
    :param exception
    :returns type, file, and line number
    """
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    return exc_type, fname, exc_tb.tb_lineno


def download_image(url):
    logging.debug(f"downloading image: {url}")
    response = requests.get(url)
    response.raise_for_status()
    return response.content


def base64_encode_long_string(long_string):
    long_string_bytes = long_string.encode('utf-8')
    encoded_bytes = base64.b64encode(long_string_bytes)
    encoded_string = encoded_bytes.decode('utf-8')
    return encoded_string


def convo_first_status_id(mastodon_api, in_reply_to_id):
    first_status = False
    last_status_id = in_reply_to_id
    while not first_status:
        last_status = mastodon_api.status(last_status_id)
        last_status_in_reply_to_id = last_status["in_reply_to_id"]
        if last_status_in_reply_to_id == None:
            first_status = True
        else:
            last_status_id = last_status_in_reply_to_id

    status_id = last_status_id
    return status_id

def get_image_response_content(mastodon_api, openai_api_key, image_url, filtered_content, media_ids):

    image_ai = openai.OpenAiImage(openai_api_key)

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

    ai_media_post = mastodon_api.media_post(
        media_file=image_result,
        file_name=image_name,
        mime_type="mime_type='image/png'",
    )
    media_ids.append(ai_media_post["id"])
    response_content = f"Image Generated from: {filtered_content}"
    return response_content