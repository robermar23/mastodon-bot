import os
import logging
import boto3
import xml.etree.ElementTree as ET
from botocore.exceptions import BotoCoreError, ClientError
from botocore.exceptions import ClientError
from contextlib import closing
from tempfile import gettempdir


defaultRegion = "us-east-1"
defaultUrl = f"https://polly.{defaultRegion}.amazonaws.com"
defaultProfile = ""


class PollyWrapper:
    def __init__(self, access_key_id: str, access_secret_key: str, regionName: str = defaultRegion, endpointUrl: str = defaultUrl, profile_name: str = defaultProfile):

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
            'polly', region_name=regionName, endpoint_url=endpointUrl)

    def start_speak(self, text: str, output_bucket: str, output_key_prefix: str, format: str = 'mp3', voice_id: str = 'Brian'):

        task_id = None

        try:

            # Specify the voice and other synthesis parameters
            language_code = 'en-US'

            text_type = "text"
            if self.is_valid_sml(text):
                text_type = "ssml"

            # Start the speech synthesis task
            response = self.polly.start_speech_synthesis_task(
                OutputFormat=format,
                OutputS3BucketName=output_bucket,
                OutputS3KeyPrefix=output_key_prefix,
                Text=text,
                VoiceId=voice_id,
                LanguageCode=language_code,
                TextType=text_type
            )

            # Retrieve the task ID for status lookups
            task_id = response['SynthesisTask']['TaskId']

        except (BotoCoreError, ClientError) as e:
            # The service returned an error, exit gracefully
            logging.error(f"aws polly error, {e.error}")
            raise e

        return task_id

    def speak(self, text: str, out_file: str, format: str = 'mp3', voice_id: str = 'Brian'):
        try:
            text_type = "text"
            if self.is_valid_sml(text):
                text_type = "ssml"

            # Request speech synthesis
            response = self.polly.synthesize_speech(
                Text=text, OutputFormat=format, VoiceId=voice_id, TextType=text_type)

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
                        logging.error(f"Could not write to file: {error}")
                        raise error
            else:
                # The response didn't contain audio data, exit gracefully
                logging.error("Could not stream audio")

        except ClientError as et:
            logging.error(f"aws polly error, {et.response}")
            if et.response['Error']['Code'] == 'TextLengthExceededException':
                # return false so caller knows to try async job method
                return False
            else:
                raise et

        except (BotoCoreError) as e:
            # The service returned an error, exit gracefully
            logging.error(f"aws polly error, {e.error}")
            raise e

    def get_voices(self):
        result = self.polly.describe_voices()
        return result["Voices"]

    def is_valid_sml(self, sml_string):
        try:
            ET.fromstring(sml_string)
            return True
        except ET.ParseError:
            return False
