from dataclasses import dataclass

@dataclass
class ListenerConfig:
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
        self.rq_queue_name = kwargs.get("rq_queue_name", None)
        self.rq_queue_retry_attempts = kwargs.get("rq_queue_retry_attempts", 3)
        self.rq_queue_retry_delay = kwargs.get("rq_queue_retry_delay", 60)
        self.rq_queue_task_timeout = kwargs.get("rq_queue_task_timeout", 3600)
        self.mastodon_s3_bucket_name = kwargs.get("mastodon_s3_bucket_name", None)
        self.mastodon_s3_bucket_prefix_path = kwargs.get("mastodon_s3_bucket_prefix_path", "/")
        self.mastodon_s3_access_key_id = kwargs.get("mastodon_s3_access_key_id", None)
        self.mastodon_s3_access_secret_key = kwargs.get("mastodon_s3_access_secret_key", None)


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

    def set_rq_queue_name(self, rq_queue_name):
        self.rq_queue_name = rq_queue_name

    def get_rq_queue_name(self):
        return self.rq_queue_name
    
    def get_rq_queue_retry_attempts(self):
        return self.rq_queue_retry_attempts
    
    def set_rq_queue_retry_attempts(self, rq_queue_retry_attempts):
        self.rq_queue_retry_attempts = rq_queue_retry_attempts
    
    def get_rq_queue_retry_delay(self):
        return self.rq_queue_retry_delay
    
    def set_rq_queue_retry_delay(self, rq_queue_retry_delay):
        self.rq_queue_retry_delay = rq_queue_retry_delay

    def get_mastodon_s3_bucket_name(self):
        return self.mastodon_s3_bucket_name

    def set_mastodon_s3_bucket_name(self, mastodon_s3_bucket_name):
        self.mastodon_s3_bucket_name = mastodon_s3_bucket_name
    
    def get_mastodon_s3_bucket_prefix_path(self):
        return self.mastodon_s3_bucket_prefix_path
    
    def set_mastodon_s3_bucket_prefix_path(self, mastodon_s3_bucket_prefix_path):
        self.mastodon_s3_bucket_prefix_path = mastodon_s3_bucket_prefix_path
    
    def get_mastodon_s3_access_key_id(self):
        return self.mastodon_s3_access_key_id
    
    def set_mastodon_s3_access_key_id(self, mastodon_s3_access_key_id):
        self.mastodon_s3_access_key_id = mastodon_s3_access_key_id
    
    def get_mastodon_s3_access_secret_key(self):
        return self.mastodon_s3_access_secret_key
    
    def set_mastodon_s3_access_secret_key(self, mastodon_s3_access_secret_key):
        self.mastodon_s3_access_secret_key = mastodon_s3_access_secret_key
    
    def get_rq_queue_task_timeout(self):
        return self.rq_queue_task_timeout
    
    def set_rq_queue_task_timeout(self, rq_queue_task_timeout):
        self.rq_queue_task_timeout = rq_queue_task_timeout
        