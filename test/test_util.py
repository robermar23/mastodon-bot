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

    def test_download_remote_file(self):
        from mastodon_bot.util import download_remote_file
        import requests

        mock_download_remote_file = requests.Response()
        mock_download_remote_file._content = b'this will be image encoded'
        mock_download_remote_file.status_code = 200

        with patch('requests.get', return_value=mock_download_remote_file) as mock_get:
            response = download_remote_file("http://www.example.com/image.png")

            self.assertEqual(response, b'this will be image encoded')
            mock_get.assert_called_once_with('http://www.example.com/image.png')

    def test_split_string_into_words(self):
        from mastodon_bot.util import split_string_by_words

        test_string = "I'm sorry, but as a friendly assistant who works for a financial investment newsletter marketing company, my role is to provide marketing solutions and ideas to improve customer engagement, not individual investment advice. It is important to perform thorough research and analysis before making any investment decisions. It's always a good idea to consult with a licensed financial advisor or broker who can provide you with personalized investment advice based on your individual financial situation, goals, and objectives."
        split = split_string_by_words(text=test_string, max_length=500)
        self.assertEqual(len(split), 2)
        self.assertEqual(split[0], "I'm sorry, but as a friendly assistant who works for a financial investment newsletter marketing company, my role is to provide marketing solutions and ideas to improve customer engagement, not individual investment advice. It is important to perform thorough research and analysis before making any investment decisions. It's always a good idea to consult with a licensed financial advisor or broker who can provide you with personalized investment advice based on your individual financial")
        self.assertEqual(split[1], "situation, goals, and objectives.")

    def test_break_long_string_into_paragraphs(self):
        from mastodon_bot.util import break_long_string_into_paragraphs

        test_string = "With billions of API calls made every day, understanding API architecture styles had never been more important. In this video, we take a closer look at these styles. They're the backbone of our interconnected digital world. APIs, or Application Programming Interfaces, play a pivotal role in modern software development. They act as bridges, allowing distinct software components to communicate and interact. They're responsible for data exchange, function calls, and overall integration between different software systems. To facilitate these operations, there exist several architectural styles, each with its own design philosophy and use cases. First, we have SOAP. It's a veteran in the field, mature, comprehensive, and XML-based. SOAP is heavily used in financial services and payment gateways, where security and reliability are key. However, if you're working on a lightweight mobile app or a quick prototype, SOAP might be overkill. It is complex and verbose. Then there's RESTful APIs. They are like the internet backbone, popular and easy to implement. It's built on top of the HTTP methods. Most of the web services you interact with daily, like Twitter or YouTube, are powered by RESTful APIs. But if you need real-time data or operate with a highly connected data model, REST might not be the best fit. Now, let's turn our attention to GraphQL. It's not just an architectural style, but also a query language. It allows clients to ask for specific data as they need. This means no more overfetching or underfetching of data. You ask for exactly what you need. This leads to more efficient network communication and faster responses. Facebook developed GraphQL to deliver efficient and precise data to its billions of users. Now it's used by companies like GitHub and Shopify. Its flexibility and efficiency make it a strong choice for applications with complex data requirements. But GraphQL does come with a steep learning curve. It also requires more processing on the server side due to its flexible querying capabilities. Let's talk about gRPC next. It's modern and high-performance. It uses protocol buffers by default. It's a favorite for microservices architectures, and companies like Netflix use gRPC to handle their inter-service communication. However, if you are dealing with browser clients, gRPC might pose some challenges due to limited browser support. WebSocket is all about real-time, bidirectional, and persistent connections. It's perfect for live chat applications and real-time gaming, where low-latency data exchange is crucial. But if your application doesn't require real-time data, using WebSocket might be an unnecessary overhead. Lastly, we have Webhook. It's all about being event-driven. It uses HTTP callbacks to provide asynchronous operations. For instance, GitHub uses Webhooks to notify other systems whenever a new commit is pushed. However, if we need synchronous communication or immediate response, Webhook might not be the best bet. And there you have it. A quick tour of the most-used API architecture styles. Remember, there's no one-size-fits-all solution. Tailor our approach to the unique project requirements. And happy coding! If you like our videos, you may like our system design newsletter as well. It covers topics and trends in large-scale system design. Trusted by 350,000 readers. Subscribe at blog.bybygo.com."
        split = break_long_string_into_paragraphs(long_string=test_string, sentences_per_paragraph=4)
        self.assertEqual(len(split), 13)




    