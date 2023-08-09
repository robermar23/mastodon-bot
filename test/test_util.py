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

        test_string = "To create a new effort in WMC, follow these steps:\n1. Select \"Create\" and choose \"Effort\".\n2. Define a name for the effort. This is a required field and it is important to use a clear and consistent naming convention.\n3. Add the date when the effort is going live.\n4. If you know the time when the effort is going out, add it as well.\n5. Define the effort destination:\n- Internal: If our company owns the outlet, which refers to our affiliates list or website.\n- Agora: If another Agora company owns the outlet, which refers to another Agora affiliates list or website.\n- Non-Agora: If a company outside of Agora owns the outlet, which refers to a 3rd party list or website.\n6. Specify the marketing destination by selecting the media outlet for this effort. For example, if you are promoting a dedicated promotion to your eletter, enter the name of your eletter.\nNote: The list must be added under Media Outlets prior to selecting it here.\n7. Define what you are promoting through this effort.\nNote: The item must be added under Media Outlets prior to selecting it here.\n8. Select the type of promotion you are creating (Effort Type).\n9. Define how you acquired the customer (Acquisition Method). Common methods include UI (User Interface) and UX (User Experience).\n10. Define the media channel. For Lead Gen, it should always be \"X\".\n11. If you selected the effort destination as Agora, you can choose to share this effort with another Agora company.\n12. Identify the appropriate domain by selecting it from the available list of domains.\n13. Define the customer journey for this effort. You can select a specific journey or choose \"test\" depending on what you want the customer to see.\n14. By default, a campaign code is selected, but you can change it if necessary. Type in the first 4 characters of the campaign code you want to use to search for valid values.\n15. The promotion description will be populated, but you can edit it as needed.\n16. Specify the spend revenue allocation based on the following options:\n- I didn't pay anything for the marketing.\n- I'm paying a flat rate: Enter the amount spent for this promotion in the amount spent field.\n- CPA (Cost per Acquisition): Enter the amount spent per lead in the amount spent field.\n- CPM (Cost per 1000 views): Enter the amount spent per 1000 views in the amount spent field.\n- I'm splitting the revenue with someone: Enter the shared information in the fields for your affiliate and partner.\n17. If you are doing a revenue share, enter the accounting code for the affiliate and the percentage that should be paid out in the Host Department 1 & '%' fields.\n18. Query parameters can be added to the effort level to append the generated link for this effort. You can store them ahead and apply them to efforts or add them on the fly.\n19. Add tags as necessary.\n20. Click on \"Generate Promo Code\" in the top right corner of the screen.\n21. Once the promo code is generated, you'll see the Effort Link at the bottom of the screen.\n22. Select \"Save\".\n23. Your effort is now saved, and you can view the results on the effort listing screen by selecting the back arrow.\nIf you need further assistance, please open a Support ticket."
        split = split_string_by_words(text=test_string, max_length=493)
        self.assertEqual(len(split), 8)


    def test_break_long_string_into_paragraphs(self):
        from mastodon_bot.util import break_long_string_into_paragraphs

        test_string = "With billions of API calls made every day, understanding API architecture styles had never been more important. In this video, we take a closer look at these styles. They're the backbone of our interconnected digital world. APIs, or Application Programming Interfaces, play a pivotal role in modern software development. They act as bridges, allowing distinct software components to communicate and interact. They're responsible for data exchange, function calls, and overall integration between different software systems. To facilitate these operations, there exist several architectural styles, each with its own design philosophy and use cases. First, we have SOAP. It's a veteran in the field, mature, comprehensive, and XML-based. SOAP is heavily used in financial services and payment gateways, where security and reliability are key. However, if you're working on a lightweight mobile app or a quick prototype, SOAP might be overkill. It is complex and verbose. Then there's RESTful APIs. They are like the internet backbone, popular and easy to implement. It's built on top of the HTTP methods. Most of the web services you interact with daily, like Twitter or YouTube, are powered by RESTful APIs. But if you need real-time data or operate with a highly connected data model, REST might not be the best fit. Now, let's turn our attention to GraphQL. It's not just an architectural style, but also a query language. It allows clients to ask for specific data as they need. This means no more overfetching or underfetching of data. You ask for exactly what you need. This leads to more efficient network communication and faster responses. Facebook developed GraphQL to deliver efficient and precise data to its billions of users. Now it's used by companies like GitHub and Shopify. Its flexibility and efficiency make it a strong choice for applications with complex data requirements. But GraphQL does come with a steep learning curve. It also requires more processing on the server side due to its flexible querying capabilities. Let's talk about gRPC next. It's modern and high-performance. It uses protocol buffers by default. It's a favorite for microservices architectures, and companies like Netflix use gRPC to handle their inter-service communication. However, if you are dealing with browser clients, gRPC might pose some challenges due to limited browser support. WebSocket is all about real-time, bidirectional, and persistent connections. It's perfect for live chat applications and real-time gaming, where low-latency data exchange is crucial. But if your application doesn't require real-time data, using WebSocket might be an unnecessary overhead. Lastly, we have Webhook. It's all about being event-driven. It uses HTTP callbacks to provide asynchronous operations. For instance, GitHub uses Webhooks to notify other systems whenever a new commit is pushed. However, if we need synchronous communication or immediate response, Webhook might not be the best bet. And there you have it. A quick tour of the most-used API architecture styles. Remember, there's no one-size-fits-all solution. Tailor our approach to the unique project requirements. And happy coding! If you like our videos, you may like our system design newsletter as well. It covers topics and trends in large-scale system design. Trusted by 350,000 readers. Subscribe at blog.bybygo.com."
        split = break_long_string_into_paragraphs(long_string=test_string, sentences_per_paragraph=4)
        self.assertEqual(len(split), 13)




    