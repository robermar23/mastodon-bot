# import ffmpeg
# import numpy as np
from pytube import YouTube
from pathlib import Path


# def load_audio(file_bytes: bytes, sr: int = 16_000) -> np.ndarray:
#     """
#     Use file's bytes and transform to mono waveform, resampling as necessary
#     Parameters
#     ----------
#     file: bytes
#         The bytes of the audio file
#     sr: int
#         The sample rate to resample the audio if necessary
#     Returns
#     -------
#     A NumPy array containing the audio waveform, in float32 dtype.
#     """
#     try:
#         # This launches a subprocess to decode audio while down-mixing and resampling as necessary.
#         # Requires the ffmpeg CLI and `ffmpeg-python` package to be installed.
#         out, _ = (
#             ffmpeg.input('pipe:', threads=0)
#             .output("pipe:", format="s16le", acodec="pcm_s16le", ac=1, ar=sr)
#             .run_async(pipe_stdin=True, pipe_stdout=True)
#         ).communicate(input=file_bytes)

#     except ffmpeg.Error as e:
#         raise RuntimeError(f"Failed to load audio: {e.stderr.decode()}") from e

#     return np.frombuffer(out, np.int16).flatten().astype(np.float32) / 32768.0

def download_youtube_audio(url,  filename = None, out_dir = "."):
    "Download the audio from a YouTube video"
    yt = YouTube(url)
    if filename is None:
        filename = Path(out_dir, to_snake_case(yt.title)).with_suffix(".mp4")
        
    yt = (yt.streams
            .filter(only_audio = True, file_extension = "mp4")
            .order_by("abr")
            .desc())
    return yt.first().download(filename = filename)

def to_snake_case(name):
    return name.lower().replace(" ", "_").replace(":", "_").replace("__", "_")