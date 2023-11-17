# import os
import openai
import base64
import logging
import tiktoken
from PIL import Image
from io import BytesIO
from mastodon_bot.timed_dict import timed_dict
from mastodon_bot.redis_timed_dict import redis_timed_dict
from mastodon_bot.util import base64_encode_long_string

class OpenAiPrompt:
    """
    Interact with OpenAI's completion interface using prompts
    """

    def __init__(self, **kwargs):
        self.model = kwargs.get("model", "text-davinci-003")
        self.temperature = kwargs.get("temperature", 0.9)
        self.max_tokens = kwargs.get("max_tokens", 2048)
        self.top_p = kwargs.get("top_p", 1.0)
        self.frequency_penalty = kwargs.get("frequency_penalty", 0.0)
        self.presence_penalty = kwargs.get("presence_penalty", 0.0)
        self.api_key = kwargs.get("openai_api_key", None)
        self.context = timed_dict(max_age_hours=kwargs.get("max_age_hours", 1))

        if self.api_key is None:
            raise ValueError("openai_api_key is required")

        if self.context.max_age_hours is None:
            raise ValueError("max_age_hours is required")

        openai.api_key = self.api_key

    def estimate_tokens(self, text):
        """
        As per https://openai.com/api/pricing/, prices are per 1,000 tokens.
        You can think of tokens as pieces of words, where 1,000 tokens is about 750 words.
        This paragraph is 35 tokens.
        :param text:
        :return:
        """
        return len(text.split()) / 0.75

    def reduce_context(self, context, limit=3000):
        new_size = int(limit / 0.75)
        return " ".join(context.split()[-new_size:]).split(".", 1)[-1]

    def create(self, prompt: str, convo_id: str, keep_context=True):
        """
        Prompt chat for a response, maintaining context of conversation by default
        """

        result = None

        logging.debug(f"creating chat with prompt {prompt}")

        try:
            tmp_context: str = ""
            if convo_id in self.context:
                tmp_context = self.context[convo_id]

            estimate_tokens_context = self.estimate_tokens(text=tmp_context)
            if estimate_tokens_context >= self.max_tokens * 0.95:
                logging.debug(
                    f"context size exceeded! context\n'''{tmp_context}'''")
                logging.debug(estimate_tokens_context)

                self.context[convo_id] = self.reduce_context(tmp_context)
                logging.debug(f"Reduced context to: {self.context}")

            estimate_tokens_prompt = self.estimate_tokens(prompt)
            if estimate_tokens_prompt >= self.max_tokens * 0.95:
                logging.debug(f"prompt size exceeded! prompt\n'''{prompt}'''")
                logging.debug(estimate_tokens_prompt)

                prompt = self.reduce_context(prompt)
                logging.debug(f"Reduced prompt to: {prompt}")

            # for maintaining context/history of chat, using passed convo_id as key
            if keep_context:
                if tmp_context.startswith("context:"):
                    self.context[convo_id] = f"{tmp_context} prompt: {prompt}"
                else:
                    self.context[convo_id] = f"context: {tmp_context} prompt: {prompt}"
                self.context.remove_old_items()
            else:
                self.context = {}

            # for understanding what each attr means
            # https://beta.openai.com/docs/api-reference/completions/create

            response = openai.chat.completions.create(
                model=self.model,
                prompt=self.context[convo_id],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=self.top_p,
                frequency_penalty=self.frequency_penalty,
                presence_penalty=self.presence_penalty,
            )

            if "choices" in response and len(response["choices"]) > 0:
                result = response["choices"][0].text

            else:
                logging.debug(f"response unexpected: {response}")

            return result
        except openai.APIConnectionError as e:
            logging.error(
                f"open api error,The server could not be reached, error: {e.__cause__}"
            )
            return "OpenAI API Connection Error"
        except openai.RateLimitError as e:
            logging.error(
                f"open api error, A 429 status code was received; we should back off a bit"
            )
            return "A 429 status code was received; we should back off a bit"
        except openai.APIStatusError as e:
            logging.error(
                f"open api error, http_status: {e.status_code}, error: {e.response}"
            )
            return "beep bop. bot beep. Dave? Dave what is going on?"


class OpenAiChat:
    """
    Interact with OpenAI's chat completion interface
    """

    def __init__(self, **kwargs):
        self.model = kwargs.get("model", "gpt-3.5-turbo")
        self.temperature = kwargs.get("temperature", 0)
        self.max_tokens = kwargs.get("max_tokens", 4096)
        self.persona = kwargs.get("persona", "You are a helpful assistant")
        self.persona_key = base64_encode_long_string(self.persona)
        # self.top_p = kwargs.get("top_p", 1.0)
        # self.frequency_penalty = kwargs.get("frequency_penalty", 0.0)
        # self.presence_penalty = kwargs.get("presence_penalty", 0.0)
        self.api_key = kwargs.get("openai_api_key", None)
        self.max_age_hours = kwargs.get("max_age_hours", 1)

        self.redis_connection = kwargs.get("redis_connection", None)
        if self.redis_connection:
            self.context = redis_timed_dict(
                redis_connection=self.redis_connection, key=self.persona_key, max_age_hours=self.max_age_hours)
        else:
            self.context = timed_dict(max_age_hours=self.max_age_hours)

        if self.api_key is None:
            raise ValueError("openai_api_key is required")

        if self.context.max_age_hours is None:
            raise ValueError("max_age_hours is required")

        try:
            self.encoding = tiktoken.encoding_for_model(self.model)
        except KeyError:
            self.encoding = tiktoken.get_encoding("gpt-3.5-turbo")

        openai.api_key = self.api_key

    def num_tokens_from_messages(self, messages: list):
        # Returns the number of tokens used by a list of messages.
        # if (
        #     self.model == "gpt-3.5-turbo-0301"
        # ):  # note: future models may deviate from this
            num_tokens = 0
            for message in messages:
                # every message follows <im_start>{role/name}\n{content}<im_end>\n
                num_tokens += 4
                # logging.debug(f"message: {message}")
                # logging.debug(f"message type: {type(message)}")

                for key, value in message.items():
                    num_tokens += len(self.encoding.encode(value))
                    if key == "name":  # if there's a name, the role is omitted
                        num_tokens += -1  # role is always required and always 1 token
            num_tokens += 2  # every reply is primed with <im_start>assistant
            return num_tokens
        # else:
        #     raise NotImplementedError(
        #         f"""num_tokens_from_messages() is not presently implemented for model {self.model}.
        #             See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens."""
        #     )

    def reduce_messages(self, messages: list, max_tokens=4096):
        cur_tokens = self.num_tokens_from_messages(messages)
        mod_tokens = cur_tokens
        while mod_tokens > max_tokens:
            messages.pop()
            mod_tokens = self.num_tokens_from_messages(messages=messages)
        return cur_tokens, mod_tokens

    def create(self, prompt: str, convo_id: str):
        """
        Prompt chat for a response, maintaining context of conversation by default
        """

        result = None

        logging.debug(f"creating chat with prompt {prompt}")

        # Example OpenAI Python library request
        # MODEL = "gpt-3.5-turbo"
        # response = openai.ChatCompletion.create(
        #     model=MODEL,
        #     messages=[
        #         {"role": "system", "content": "You are a helpful assistant."},
        #         {"role": "user", "content": "Knock knock."},
        #         {"role": "assistant", "content": "Who's there?"},
        #         {"role": "user", "content": "Orange."},
        #     ],
        #     temperature=0,
        # )

        try:
            tmp_messages = []
            if convo_id in self.context:
                tmp_messages = self.context[convo_id]
            
            # logging.debug(f"cached messages: {tmp_messages}")
            # logging.debug(f"messages type: {type(tmp_messages)}")

            cur_tokens, mod_tokens = self.reduce_messages(
                messages=tmp_messages)
            if cur_tokens > mod_tokens:
                logging.debug(
                    f"max tokens exceeded! reduced by\n'''{cur_tokens - mod_tokens}'''"
                )

            # for maintaining context/history of chat, using passed convo_id as key
            msg_len = len(tmp_messages)
            if msg_len < 3:
                tmp_messages = self.init_messages(prompt=prompt)
            # elif msg_len == 1:
            #     tmp_messages = self.init_messages(prompt=prompt)
            # elif msg_len == 2:
            #     tmp_messages = self.init_messages(prompt=prompt)
            else:
                tmp_messages = self.append_prompt(
                    messages=tmp_messages, prompt=prompt)

            response = openai.chat.completions.create(
                model=self.model, messages=tmp_messages, temperature=self.temperature
            )

            if "choices" in response and len(response["choices"]) > 0:
                if "message" in response["choices"][0]:
                    if "content" in response["choices"][0]["message"]:
                        result = response["choices"][0]["message"]["content"]
                    else:
                        logging.debug(f"response unexpected: {response}")
                else:
                    logging.debug(f"response unexpected: {response}")
            else:
                logging.debug(f"response unexpected: {response}")

            self.context[convo_id] = self.append_response(
                messages=tmp_messages, response=result
            )

            return result

        except openai.APIConnectionError as e:
            logging.error(
                f"open api error,The server could not be reached, error: {e.__cause__}"
            )
            raise e
        except openai.RateLimitError as e:
            logging.error(
                f"open api error, A 429 status code was received; we should back off a bit"
            )
            raise e
        except openai.APIStatusError as e:
            logging.error(
                f"open api error, http_status: {e.status_code}, error: {e.response}"
            )
            raise e

    def init_messages(self, prompt):
        result = []
        result.append({"role": "system", "content": self.persona})
        result.append({"role": "user", "content": prompt})
        return result

    def append_prompt(self, messages: list, prompt: str):
        messages.append({"role": "user", "content": prompt})
        return messages

    def append_response(self, messages: list, response: str):
        messages.append({"role": "assistant", "content": response})
        return messages


class OpenAiImage:
    """
    Interact with OpenAI's image endpoint
    """

    def __init__(self, openai_api_key):
        self.n = 1
        self.width = 1024
        self.height = 1024
        self.size = f"{self.height}x{self.width}"
        self.api_key = openai_api_key
        self.response_format = "b64_json"
        openai.api_key = self.api_key

    def create(self, prompt):
        """
        Prompt chat for an image
        """

        result = None

        logging.debug(f"creating image with prompt {prompt}")

        try:
            # https://beta.openai.com/docs/api-reference/images/create
            response = openai.images.generate(
                model="dall-e-3",
                prompt=prompt,
                n=self.n,
                size=self.size,
                response_format=self.response_format,
            )

            if "data" in response and len(response["data"]) > 0:
                b64 = response["data"][0].b64_json
                result = base64.b64decode(b64)
            else:
                logging.debug(f"response unexpected: {response}")

            return result

        except openai.APIConnectionError as e:
            logging.error(
                f"open api error,The server could not be reached, error: {e.__cause__}"
            )
            return "OpenAI API Connection Error"
        except openai.RateLimitError as e:
            logging.error(
                f"open api error, A 429 status code was received; we should back off a bit"
            )
            return "A 429 status code was received; we should back off a bit"
        except openai.APIStatusError as e:
            logging.error(
                f"open api error, http_status: {e.status_code}, error: {e.response}"
            )
            return "beep bop. bot beep. Dave? Dave what is going on?"

    def variation(self, image):
        """
        Prompt chat for an image variation of an existing image
        """

        result = None

        logging.debug("creating variation of image")

        with Image.open(BytesIO(image)) as img_convert:

            # for size to match our intended, ignoring aspect ratio for now
            img_convert = img_convert.resize((self.width, self.height))

            # convert to png for submission, if necessary
            if img_convert.format != "PNG":
                logging.debug(
                    f"converting image to png as format is {img_convert.format}"
                )
                img_convert = img_convert.convert("RGB")

            img_buffer = BytesIO()
            img_convert.save(img_buffer, format="PNG")
            img_buffer.seek(0)

            try:
                # https://beta.openai.com/docs/api-reference/images/create-variation
                response = openai.images.create_variation(
                    model="dall-e-2",
                    image=img_buffer,
                    n=self.n,
                    size=self.size,
                    response_format=self.response_format,
                )

                if "data" in response and len(response["data"]) > 0:
                    b64 = response["data"][0].b64_json
                    result = base64.b64decode(b64)

                return result

            except openai.APIConnectionError as e:
                logging.error(
                    f"open api error,The server could not be reached, error: {e.__cause__}"
                )
                raise e
            except openai.RateLimitError as e:
                logging.error(
                    f"open api error, A 429 status code was received; we should back off a bit"
                )
                raise e
            except openai.APIStatusError as e:
                logging.error(
                    f"open api error, http_status: {e.status_code}, error: {e.response}"
                )
                raise e

class OpenAiTranscribe:
    """
    Interact with OpenAI's transcribe endpoint
    """

    def __init__(self, openai_api_key, model="whisper-1"):
        self.api_key = openai_api_key
        self.model = model
        openai.api_key = self.api_key

    def create(self, audio_file):
        """
        Prompt chat to transcribe
        """

        result = None

        logging.debug(f"creating transcription from audio file")

        try:
            audio = open(audio_file, "rb")
            result = openai.audio.transcriptions.create(self.model, audio)

            return result.text

        except openai.APIConnectionError as e:
            logging.error(
                f"open api error,The server could not be reached, error: {e.__cause__}"
            )
            raise e
        except openai.RateLimitError as e:
            logging.error(
                f"open api error, A 429 status code was received; we should back off a bit"
            )
            raise e
        except openai.APIStatusError as e:
            logging.error(
                f"open api error, http_status: {e.status_code}, error: {e.response}"
            )
            raise e

        
