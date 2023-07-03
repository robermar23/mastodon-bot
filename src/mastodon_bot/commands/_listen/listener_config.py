from dataclasses import dataclass

@dataclass
class ListenerConfig():
    def __init__(self, **kwargs):

        self.openai_api_key = kwargs.get("openai_api_key", None)
        self.response_type = kwargs.get("response_type", None)
        self.chat_model = kwargs.get("chat_model", None)
        self.chat_temperature = kwargs.get("chat_temperature", None)
        self.chat_max_tokens = kwargs.get("chat_max_tokens", None)
        self.chat_top_p = kwargs.get("chat_top_p", None)
        self.chat_frequency_penalty = kwargs.get(
            "chat_frequency_penalty", None)
        self.chat_presence_penalty = kwargs.get("chat_presence_penalty", None)
        self.chat_max_age_hours_context = kwargs.get(
            "chat_max_age_hours_context", None)
        self.chat_persona = kwargs.get("chat_persona", None)
        self.mastodon_client_id = kwargs.get("mastodon_client_id", None)
        self.mastodon_client_secret = kwargs.get(
            "mastodon_client_secret", None)
        self.mastodon_access_token = kwargs.get("mastodon_access_token", None)
        self.mastodon_host = kwargs.get("mastodon_host", None)
        self.rq_redis_connection = kwargs.get("rq_redis_connection", None)

    def get_openai_api_key(self):
        return self.openai_api_key
    
    def set_openai_api_key(self, openai_api_key):
        self.openai_api_key = openai_api_key

    def get_response_type(self):
        return self.response_type

    def set_response_type(self, response_type):
        self.response_type = response_type
    
    def get_chat_model(self):
        return self.chat_model

    def set_chat_model(self, chat_model):
        self.chat_model = chat_model

    def get_chat_temperature(self):
        return self.chat_temperature
    
    def set_chat_temperature(self, chat_temperature):
        self.chat_temperature = chat_temperature

    def get_chat_max_tokens(self):
        return self.chat_max_tokens
    
    def set_chat_max_tokens(self, chat_max_tokens):
        self.chat_max_tokens = chat_max_tokens

    def get_chat_top_p(self):
        return self.chat_top_p
    
    def set_chat_top_p(self, chat_top_p):
        self.chat_top_p = chat_top_p

    def get_chat_frequency_penalty(self):
        return self.chat_frequency_penalty
    
    def set_chat_frequency_penalty(self, chat_frequency_penalty):
        self.chat_frequency_penalty = chat_frequency_penalty

    def get_chat_presence_penalty(self):
        return self.chat_presence_penalty
    
    def set_chat_presence_penalty(self, chat_presence_penalty):
        self.chat_presence_penalty = chat_presence_penalty

    def get_chat_max_age_hours_context(self):
        return self.chat_max_age_hours_context
    
    def set_chat_max_age_hours_context(self, chat_max_age_hours_context):
        self.chat_max_age_hours_context = chat_max_age_hours_context

    def get_chat_persona(self):
        return self.chat_persona
    
    def set_chat_persona(self, chat_persona):
        self.chat_persona = chat_persona

    def get_mastodon_client_id(self):
        return self.mastodon_client_id
    
    def set_mastodon_client_id(self, mastodon_client_id):
        self.mastodon_client_id = mastodon_client_id
    
    def get_mastodon_client_secret(self):
        return self.mastodon_client_secret
    
    def set_mastodon_client_secret(self, mastodon_client_secret):
        self.mastodon_client_secret = mastodon_client_secret

    def get_mastodon_access_token(self):
        return self.mastodon_access_token
    
    def set_mastodon_access_token(self, mastodon_access_token):
        self.mastodon_access_token = mastodon_access_token

    def get_mastodon_host(self):
        return self.mastodon_host
    
    def set_mastodon_host(self, mastodon_host):
        self.mastodon_host = mastodon_host

    def get_rq_redis_connection(self):
        return self.rq_redis_connection
    
    def set_rq_redis_connection(self, rq_redis_connection):
        self.rq_redis_connection = rq_redis_connection
        
    
