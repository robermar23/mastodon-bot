import enum

class ListenerResponseType(enum.Enum):
    REVERSE_STRING = 1
    OPEN_AI_CHAT = 2
    OPEN_AI_IMAGE = 3
    OPEN_AI_PROMPT = 4
    OPEN_AI_TRANSCRIBE = 5
    TEXT_TO_SPEECH = 6