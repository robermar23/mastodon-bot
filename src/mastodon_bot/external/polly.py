"""
This module contains the wrapper class for AWS Polly.
"""
import os
import logging
from contextlib import closing
from tempfile import gettempdir
import boto3
from botocore.exceptions import BotoCoreError, ClientError

DEFAULT_REGION = "us-east-1"
DEFAULT_URL = f"https://polly.{DEFAULT_REGION}.amazonaws.com"
DEFAULT_PROFILE = ""


class PollyWrapper:
    """
    Wrapper class for AWS Polly.
    """
    def __init__(self, access_key_id: str, access_secret_key: str, region_name: str = DEFAULT_REGION,
                 endpoint_url: str = DEFAULT_URL, profile_name: str = DEFAULT_PROFILE):

        boto3.set_stream_logger(
            name='botocore.credentials', level=logging.WARNING)
        boto3.set_stream_logger(
            name='urllib3.connectionpool', level=logging.WARNING)

        if profile_name == "":
            session = boto3.Session(
                aws_access_key_id=access_key_id,
                aws_secret_access_key=access_secret_key
            )
        else:
            session = boto3.Session(profile_name=profile_name)

        self.polly = session.client(
            'polly', region_name=region_name, endpoint_url=endpoint_url)

    def start_speak(self, text: str, output_bucket: str, output_key_prefix: str,
                    format_type: str = 'mp3', voice_id: str = 'Brian'):
        """
        Starts an asynchronous job to synthesize speech from text.
        """
        task_id = None

        try:

            # Specify the voice and other synthesis parameters
            language_code = 'en-US'

            text_type = "text"
            if self.is_valid_sml(text):
                text_type = "ssml"

            # switch to the neural engine if the voice_id supports it
            engine = self.decide_engine(voice_id)

            # Start the speech synthesis task
            response = self.polly.start_speech_synthesis_task(
                OutputFormat=format_type,
                OutputS3BucketName=output_bucket,
                OutputS3KeyPrefix=output_key_prefix,
                Text=text,
                VoiceId=voice_id,
                LanguageCode=language_code,
                TextType=text_type,
                Engine=engine
            )

            # Retrieve the task ID for status lookups
            task_id = response['SynthesisTask']['TaskId']

        except (BotoCoreError, ClientError) as e:
            # The service returned an error, exit gracefully
            logging.error("aws polly error, %s", e)
            raise e

        return task_id

    def speak(self, text: str, out_file: str, format_type: str = 'mp3', voice_id: str = 'Brian'):
        """
        Synthesizes speech from text, and saves it to a file.
        """
        try:
            text_type = "text"
            if self.is_valid_sml(text):
                text_type = "ssml"

            # switch to the neural engine if the voice_id supports it
            engine = self.decide_engine(voice_id)

            # Request speech synthesis
            response = self.polly.synthesize_speech(
                Text=text, OutputFormat=format_type, VoiceId=voice_id,
                TextType=text_type, Engine=engine)

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

                        # return true to caller to it knows to use response in outfile
                        return True

                    except IOError as error:
                        # Could not write to file, exit gracefully
                        logging.error("Could not write to file: %s", error)
                        raise error
            else:
                # The response didn't contain audio data, exit gracefully
                logging.error("Could not stream audio")

        except ClientError as et:
            logging.error("aws polly error, %s", et.response)
            if et.response['Error']['Code'] == 'TextLengthExceededException':
                # return false so caller knows to try async job method
                return False
            else:
                raise et

        except (BotoCoreError) as e:
            # The service returned an error, exit gracefully
            logging.error("aws polly error, %s", e)
            raise e

    def get_voices(self):
        """
        Returns a list of voices available for use when requesting speech synthesis.
        """
        result = self.polly.describe_voices()
        return result["Voices"]

    def is_valid_sml(self, sml_string):
        """
        Returns True if the string contains any of the tags that indicate SSML.
        """
        result = False
        any_tags = ['speak', 'break', 'emphasis', 'prosody', 'phoneme', 'amazon:domain']
        for tag in any_tags:
            opening_tag = f'<{tag}'
            closing_tag = f'</{tag}>'
            if opening_tag in sml_string and closing_tag in sml_string:
                result = True
                break
        return result

    def decide_engine(self, voice_id):
        """
        Returns the engine to use based on the voice_id.
        """
        engine = "standard"
        all_voices = self.get_voices()
        for voice in all_voices:
            if voice['Id'] == voice_id:
                if "neural" in voice['SupportedEngines']:
                    engine = "neural"
                break
        return engine
