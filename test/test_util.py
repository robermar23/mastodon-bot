import unittest
from unittest.mock import patch, Mock



class UtilTestHandler(unittest.TestCase):

    def setUp(self) -> None:
        return super().setUp()

    def test_filter_words(self):

        from mastodon_bot.util import filter_words

        test_string = "Hi, how are you doing today?"
        filtered_string = filter_words(string=test_string, starting_char="H")
        self.assertEqual(filtered_string, ["Hi,"])

        test_string = "@test @test2 test3 test4, hello world"
        filtered_string = filter_words(string=test_string, starting_char="@")
        self.assertEqual(filtered_string, ["@test", "@test2"])

    def test_split_string(self):
        from mastodon_bot.util import split_string

        test_string = "111111111122222222223333333333"
        split = split_string(string=test_string, max_length=10)
        self.assertEqual(split, ["1111111111", "2222222222", "3333333333"])

        test_string = "1111111111 2222222222 3333333333"
        split = split_string(string=test_string, max_length=10)
        self.assertEqual(split, ["1111111111", " 222222222", "2 33333333", "33"])

    def test_remove_word(self):
        from mastodon_bot.util import remove_word

        test_string = "I want to remove this word"
        removed = remove_word(string=test_string, word="this")
        self.assertEqual(removed, "I want to remove word")

        test_string = "I want to remove this word this as this appears three times"
        removed = remove_word(string=test_string, word="this")
        self.assertEqual(removed, "I want to remove word as appears three times")

    def test_download_image(self):
        from mastodon_bot.util import download_image
        import requests

        mock_download_image = requests.Response()
        mock_download_image._content = b'this will be image encoded'
        mock_download_image.status_code = 200

        with patch('requests.get', return_value=mock_download_image) as mock_get:
            response = download_image("http://www.example.com/image.png")

            self.assertEqual(response, b'this will be image encoded')
            mock_get.assert_called_once_with('http://www.example.com/image.png')

    def test_split_string_into_words(self):
        from mastodon_bot.util import split_string_by_words

        test_string = "I'm sorry, but as a friendly assistant who works for a financial investment newsletter marketing company, my role is to provide marketing solutions and ideas to improve customer engagement, not individual investment advice. It is important to perform thorough research and analysis before making any investment decisions. It's always a good idea to consult with a licensed financial advisor or broker who can provide you with personalized investment advice based on your individual financial situation, goals, and objectives."
        split = split_string_by_words(text=test_string, max_length=500)
        self.assertEqual(len(split), 2)
        self.assertEqual(split[0], "I'm sorry, but as a friendly assistant who works for a financial investment newsletter marketing company, my role is to provide marketing solutions and ideas to improve customer engagement, not individual investment advice. It is important to perform thorough research and analysis before making any investment decisions. It's always a good idea to consult with a licensed financial advisor or broker who can provide you with personalized investment advice based on your individual financial")
        self.assertEqual(split[1], "situation, goals, and objectives.")




    