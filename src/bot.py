import logging
import re
import os
import sys
from mastodon import Mastodon


logger = logging.getLogger("bot")


re_mastodon = re.compile(
    r"https?://(robermar\.net|mastodon\.social|mstdn\.jp)/\S+/\d+")
re_link = re.compile(
    r"^(?:https?://)?[\w.-]+(?:\.[\w\.-]+)+[\w\-\._~:/?#[\]@!\$&'\(\)\*\+,;=.]+$")

def error_info(e):
    """
    https://stackoverflow.com/a/1278740
    :param exception
    :returns type, file, and line number
    """
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    return exc_type, fname, exc_tb.tb_lineno