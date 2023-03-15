# import os
import openai
import base64
import logging
from PIL import Image
from io import BytesIO
from src.timed_dict import timed_dict


class OpenAiChat:
    """
    Interact with OpenAI's completion interface
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
        return " ".join(context.split()[-new_size:]).split('.', 1)[-1]
    
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
                logging.debug(f"context size exceeded! context\n'''{tmp_context}'''")
                logging.debug(estimate_tokens_context)

                self.context[convo_id] = self.reduce_context(tmp_context)
                logging.debug(f"Reduced context to: {self.context}")

            estimate_tokens_prompt = self.estimate_tokens(prompt)
            if estimate_tokens_prompt >= self.max_tokens * 0.95:
                logging.debug(f"prompt size exceeded! prompt\n'''{prompt}'''")
                logging.debug(estimate_tokens_prompt)

                prompt = self.reduce_context(prompt)
                logging.debug(f"Reduced prompt to: {prompt}")
                
            #for maintaining context/history of chat, using passed convo_id as key
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
            response = openai.Completion.create(
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
        except openai.error.OpenAIError as e:
            logging.error(
                f"open api error, http_status: {e.http_status}, error: {e.error}"
            )
            return "beep bop. bot beep. Dave? Dave what is going on?"


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
            response = openai.Image.create(
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

        except openai.error.OpenAIError as e:
            logging.error(
                f"open api error, http_status: {e.http_status}, error: {e.error}"
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
                logging.debug(f"converting image to png as format is {img_convert.format}")
                img_convert = img_convert.convert("RGB")

            img_buffer = BytesIO()
            img_convert.save(img_buffer, format="PNG")
            img_buffer.seek(0)

            try:
                # https://beta.openai.com/docs/api-reference/images/create-variation
                response = openai.Image.create_variation(
                    image=img_buffer,
                    n=self.n,
                    size=self.size,
                    response_format=self.response_format,
                )

                if "data" in response and len(response["data"]) > 0:
                    b64 = response["data"][0].b64_json
                    result = base64.b64decode(b64)

                return result
            
            except openai.error.OpenAIError as e:
                logging.error(
                    f"open api error, http_status: {e.http_status}, error: {e.error}"
                )
                return "beep bop. bot beep. Dave? Dave what is going on?"
            
    
