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

