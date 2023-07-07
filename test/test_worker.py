import unittest
from unittest.mock import patch, Mock


class UtilTestHandler(unittest.TestCase):

    def setUp(self) -> None:
        return super().setUp()

    def test_listener_respond(self):

        from mastodon_bot.worker import listener_respond
        from mastodon_bot.commands._listen.listener_config import ListenerConfig
        from mastodon_bot.commands._listen.listener_response_type import ListenerResponseType

        result = listener_respond(
            content="@agora write a python script that will scrape an array of websites, looking for a given text pattern in the home page of that website",
            in_reply_to_id=None,
            image_url="",
            status_id="110670307530238202",
            config=ListenerConfig(
                mastodon_host="dev.14west.social",
                mastodon_client_id="ZPQTIZDr6bw__nl9-FX7jlI5DQp9aasuB29ktlMOZI4",
                mastodon_client_secret="ZE7SPjooMKSBeolV1RHDJvEiPu04wvvwZMTor5-c440",
                mastodon_access_token="AHtFbQYX8Wp1hEzkiYU9i_QViLiVQQ_pmESwJgPrBOU",
                response_type=ListenerResponseType.OPEN_AI_CHAT,
                chat_model="gpt-3.5-turbo-0301",
                chat_temperature=0.9,
                chat_max_tokens=2048,
                chat_top_p=1.0,
                chat_frequency_penalty=0.0,
                chat_presence_penalty=0.0,
                chat_max_age_hours_context=24,
                chat_persona="You are an assistant who works in an Information Technology department. Focus your responses on answers pertaining to Information Technology solutions, Do not answer questions outside of Information Technology. Be detailed in your response and provide step-by-step guidance which can be implemented by analysts or systems engineers.",
                rq_redis_connection="redis://default:8ckxHVNZGnqu@mastodon-redis.devops-mastodon-dev.svc.cluster.local:6379/1",
                rq_queue_name="mastodon-bot",
                rq_queue_retry_attempts=3,
                rq_queue_retry_delay=60,
                openai_api_key="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",
                mastodon_s3_bucket_name = "14w-social-dev",
                mastodon_s3_bucket_prefix_path = "unroll/",
                mastodon_s3_access_key_id = "AKIAZNJ2XHJZWJUEXHU6",
                mastodon_s3_access_secret_key = "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"
            )
        )
        
        self.assertIsNotNone(result)
