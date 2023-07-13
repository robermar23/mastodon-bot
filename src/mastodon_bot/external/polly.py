import os
import logging
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from contextlib import closing
from tempfile import gettempdir


defaultRegion = "us-east-1"
defaultUrl = f"https://polly.{defaultRegion}.amazonaws.com"


class PollyWrapper:
    def __init__(self, access_key_id: str, access_secret_key: str, regionName: str = defaultRegion, endpointUrl: str = defaultUrl):

        session = boto3.Session(
            aws_access_key_id=access_key_id,
            aws_secret_access_key=access_secret_key
        )

        self.polly = session.client(
            'polly', region_name=regionName, endpoint_url=endpointUrl)

    def speak(self, text: str, out_file: str, format: str = 'mp3', voice_id: str = 'Brian'):
        try:
            # Request speech synthesis
            response = self.polly.synthesize_speech(
                Text=text, OutputFormat=format, VoiceId=voice_id)

            # Access the audio stream from the response
            if "AudioStream" in response:
                # Note: Closing the stream is important because the service throttles on the
                # number of parallel connections. Here we are using contextlib.closing to
                # ensure the close method of the stream object will be called automatically
                # at the end of the with statement's scope.
                with closing(response["AudioStream"]) as stream:
                    output = os.path.join(gettempdir(), out_file)

                    try:
                      # Open a file for writing the output as a binary stream
                        with open(output, "wb") as file:
                            file.write(stream.read())
                    except IOError as error:
                        # Could not write to file, exit gracefully
                        logging.error(f"Could not write to file: {error}")
                        raise error

            else:
                # The response didn't contain audio data, exit gracefully
                logging.error("Could not stream audio")

        except (BotoCoreError, ClientError) as e:
            # The service returned an error, exit gracefully
            logging.error(f"aws polly error, {e.error}")
            raise e

    def get_voices(self):
        return self.polly.describe_voices()
