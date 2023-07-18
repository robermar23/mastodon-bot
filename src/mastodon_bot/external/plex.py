import logging
import urllib.parse

from datetime import datetime, timedelta
from plexapi.server import PlexServer
from mastodon_bot.util import error_info
from mastodon_bot.util import download_remote_file


class PlexInstance:
    """
    Interact with a plex server
    """

    def __init__(self, plex_host: str, plex_token: str, plex_server_id: str):
        self.plex_host = plex_host
        self.plex_token = plex_token
        self.plex_server_id = plex_server_id

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
                    item_to_add = PlexRecentlyAddedItem(
                        media_item=media_item, server_id=self.plex_server_id
                    )
                    result.append(item_to_add)
                    logging.debug(f"Added to result: {media_item.title}")
                else:
                    logging.debug(
                        f"Not added: {media_item.title}, added {hours_age} hours ago"
                    )

        except Exception as e:
            logging.error(error_info(e))

        return result


class PlexRecentlyAddedItem:
    """
    Summary info and poster image bytes for a plex recently added item
    """

    def __init__(self, media_item, server_id: str):
        self.media_item = media_item
        self.server_id = server_id

    def get_description(self):
        desc: str = ""
        if self.media_item.type == "season":
            desc = f"A new episode was added to Plex for {self.media_item.parentTitle}!\n\n{self.get_public_uri()}"
        else:
            desc = f"A {self.media_item.type} called {self.media_item.title} was added to Plex!.\n\nSummary:\n{self.media_item.summary}\n\n{self.get_public_uri()}"
        return desc

    def get_poster_image_data(self):
        content_data, file_extension = download_remote_file(self.media_item.posterUrl)
        return content_data

    def get_post_image_file_name(self):
        return f"{self.media_item.title.replace(' ', '_')}.png"

    def get_public_uri(self):
        return f"https://app.plex.tv/desktop/#!/server/{self.server_id}/details?key={urllib.parse.quote(self.media_item.key, safe='')}&context=home%3Ahub.movie.recentlyadded~1~0"
