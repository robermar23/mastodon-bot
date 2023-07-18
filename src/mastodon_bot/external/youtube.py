from pytube import YouTube
from pathlib import Path

class YouTubeWrapper:
    """
    Interact with YouTube API
    """

    def download_youtube_audio(self, url,  filename = None, out_dir = "."):
      yt = YouTube(url)
      if filename is None:
          filename = Path(out_dir, self.to_snake_case(yt.title)).with_suffix(".mp4")
          
      yt = (yt.streams
              .filter(only_audio = True, file_extension = "mp4")
              .order_by("abr")
              .desc())
      return yt.first().download(filename = filename)

    def to_snake_case(self, name):
      return name.lower().replace(" ", "_").replace(":", "_").replace("__", "_")