import time
import os
import sys
import requests
import logging
import base64
import textwrap
import re

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

def split_string_by_words(text: str, max_length: int = 0):
    # Split the text into paragraphs and wrap each paragraph
    paragraphs = text.split('\n')
    wrapped_paragraphs = [textwrap.wrap(p, max_length) for p in paragraphs]

    # Flatten the list of wrapped paragraphs
    wrapped_text = [word for sublist in wrapped_paragraphs for word in sublist]

    # Join the wrapped text into groups of 'width' characters
    groups = []
    current_group = ''
    for word in wrapped_text:
        if len(current_group) + len(word) <= max_length:
            current_group += word
        else:
            groups.append(current_group)
            current_group = word
    if current_group:
        groups.append(current_group)

    return groups

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


def download_remote_file(url):
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

def detect_code_in_markdown(markdown_text):
    # Regular expression pattern to match code blocks in Markdown
    code_block_pattern = r"```[\w+\s]*\n([\s\S]*?)\n```"

    # Regular expression pattern to match inline code in Markdown
    inline_code_pattern = r"`([^`]+)`"

    # Find code blocks in the Markdown text
    code_blocks = re.findall(code_block_pattern, markdown_text, re.MULTILINE | re.DOTALL)

    # Find inline code in the Markdown text
    inline_code = re.findall(inline_code_pattern, markdown_text)

    return code_blocks or inline_code

# def apply_rtf_to_response(markdown_text:str):
#     # Regular expression pattern to match code blocks in Markdown
#     code_block_pattern = r"```[\w+\s]*\n([\s\S]*?)\n```"

#     # Regular expression pattern to match inline code in Markdown
#     inline_code_pattern = r"`([^`]+)`"

#     # Find code blocks in the Markdown text
#     code_blocks = re.findall(code_block_pattern, markdown_text, re.MULTILINE | re.DOTALL)

#     # Find inline code in the Markdown text
#     inline_code = re.findall(inline_code_pattern, markdown_text)

#     # Convert code blocks to RTF
#     rtf_code_blocks = []
#     for code_block in code_blocks:
#         rtf_code_blocks.append(apply_rtf_to_code_block(code_block))

#     # Convert inline code to RTF
#     rtf_inline_code = []
#     for inline_code_block in inline_code:
#         rtf_inline_code.append(apply_rtf_to_inline_code(inline_code_block))
