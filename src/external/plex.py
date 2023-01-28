import logging

from datetime import datetime, timedelta
from plexapi.server import PlexServer

from src.util import error_info
from src.util import download_image


class PlexInstance:
    """
    Interact with a plex server
    """

    def __init__(self, plex_host: str, plex_token: str):
        self.plex_host = plex_host
        self.plex_token = plex_token

    def get_recently_added(self, hours_since: int):

        result = []

        plex = PlexServer(self.plex_host, self.plex_token)

        try:
            added = plex.library.recentlyAdded()
            for media_item in added:
                item_added_at = media_item.addedAt
                now = datetime.now()
                hours_age = (now - item_added_at) / timedelta(hours=1)
                if hours_age <= hours_since:
                    item_to_add = PlexRecentlyAddedItem(media_item=media_item)
                    result.append(item_to_add)
                    logging.debug(f"Added to result: {media_item.title}")
                else:
                    logging.debug("Not added: {media_item.title}")

        except Exception as e:
            logging.error(error_info(e))

        return result


class PlexRecentlyAddedItem:
    """
    Summary info and poster image bytes for a plex recently added item
    """

    def __init__(self, media_item):
        self.media_item = media_item

    def get_description(self):
        desc: str = ""
        if self.media_item.type == "season":
            desc = f"A new episode was added to Plex for {self.media_item.parentTitle}!"
        else:
            desc = f"A {self.media_item.type} called {self.media_item.title} was added to Plex!.\n\nSummary:\n{self.media_item.summary}"
        return desc

    def get_poster_image_data(self):
        return download_image(self.media_item.posterUrl)

    def get_post_image_file_name(self):
        return f"{self.media_item.title.replace(' ', '_')}.png"
