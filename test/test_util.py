import unittest
from unittest.mock import patch, Mock



class UtilTestHandler(unittest.TestCase):

    def setUp(self) -> None:
        return super().setUp()

    def test_filter_words(self):

        from src.util import filter_words

        test_string = "Hi, how are you doing today?"
        filtered_string = filter_words(string=test_string, starting_char="H")
        self.assertEqual(filtered_string, ["Hi,"])

        test_string = "@test @test2 test3 test4, hello world"
        filtered_string = filter_words(string=test_string, starting_char="@")
        self.assertEqual(filtered_string, ["@test", "@test2"])

    def test_split_string(self):
        from src.util import split_string

        test_string = "111111111122222222223333333333"
        split = split_string(string=test_string, max_length=10)
        self.assertEqual(split, ["1111111111", "2222222222", "3333333333"])

        test_string = "1111111111 2222222222 3333333333"
        split = split_string(string=test_string, max_length=10)
        self.assertEqual(split, ["1111111111", " 222222222", "2 33333333", "33"])

    def test_remove_word(self):
        from src.util import remove_word

        test_string = "I want to remove this word"
        removed = remove_word(string=test_string, word="this")
        self.assertEqual(removed, "I want to remove word")

        test_string = "I want to remove this word this as this appears three times"
        removed = remove_word(string=test_string, word="this")
        self.assertEqual(removed, "I want to remove word as appears three times")

    def test_download_image(self):
        from src.util import download_image
        import requests

        mock_download_image = requests.Response()
        mock_download_image._content = b'this will be image encoded'
        mock_download_image.status_code = 200

        with patch('requests.get', return_value=mock_download_image) as mock_get:
            response = download_image("http://www.example.com/image.png")

            self.assertEqual(response, b'this will be image encoded')
            mock_get.assert_called_once_with('http://www.example.com/image.png')




    