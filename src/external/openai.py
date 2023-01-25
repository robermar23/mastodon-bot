#import os
import openai
import base64
import requests
from PIL import Image
from io import BytesIO


class OpenAiChat:
    def __init__(self, openai_api_key):
        self.model = "text-davinci-003"
        self.temperature = 0.9
        self.max_tokens = 2048
        self.top_p = 1.0
        self.frequency_penalty = 0.0
        self.presence_penalty = 0.0
        self.api_key = openai_api_key
        openai.api_key = self.api_key

    def create(self, prompt):
        result = None

        # for understanding what each attr means
        # https://beta.openai.com/docs/api-reference/completions/create
        response = openai.Completion.create(
            model=self.model,
            prompt=prompt,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            top_p=self.top_p,
            frequency_penalty=self.frequency_penalty,
            presence_penalty=self.presence_penalty,
        )

        if "choices" in response and len(response["choices"]) > 0:
            result = response["choices"][0].text

        return result


class OpenAiImage:
    def __init__(self, openai_api_key):
        self.n = 1
        self.width = 1024
        self.height = 1024
        self.size = f"{self.height}x{self.width}"
        self.api_key = openai_api_key
        self.response_format = "b64_json"
        openai.api_key = self.api_key

    def create(self, prompt):
        result = None

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

        return result

    def variation(self, debugging, image):
        result = None

        with Image.open(BytesIO(image)) as img_convert:
            
            #for size to match our intended, ignoring aspect ratio for now
            img_convert = img_convert.resize((self.width, self.height))

            # convert to png for submission, if necessary
            if img_convert.format != "PNG":
                img_convert = img_convert.convert("RGB")

            img_buffer = BytesIO()
            img_convert.save(img_buffer, format="PNG")
            img_buffer.seek(0)

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
