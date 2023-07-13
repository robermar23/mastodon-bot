import unittest
from unittest.mock import patch, Mock



class UtilTestHandler(unittest.TestCase):

    def setUp(self) -> None:
        return super().setUp()

    def test_get_voices(self):

        from mastodon_bot.external.polly import PollyWrapper
        
        wrapper = PollyWrapper(access_key_id="", access_secret_key="", profile_name="mastodon")
        result = wrapper.get_voices()
        self.assertIsNotNone(result)
