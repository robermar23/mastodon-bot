import unittest
from unittest.mock import patch, Mock



class PollyTestHandler(unittest.TestCase):

    def setUp(self) -> None:
        return super().setUp()

    def test_valid_ssml(self):

        from mastodon_bot.external.polly import PollyWrapper
        
        wrapper = PollyWrapper(access_key_id="", access_secret_key="", profile_name="mastodon")

        test_saml = '<speak><amazon:domain name="news">The future is here. AI is here to stay. And I even washed my hair for this video</amazon:domain></speak>'
        valid = wrapper.is_valid_sml(test_saml)
        self.assertTrue(valid)

        test_saml = 'The future is here. AI is here to stay. And I even washed my hair for this video'
        valid = wrapper.is_valid_sml(test_saml)
        self.assertFalse(valid)



#