import os
from dotenv import load_dotenv
load_dotenv()

class Settings:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    GPT4V_MODEL: str = os.getenv("GPT4V_MODEL", "gpt-4o")
    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "whisper-1")
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    KAFKA_INPUT_TOPIC: str = os.getenv("KAFKA_INPUT_TOPIC", "multimodal-events")
    KAFKA_OUTPUT_TOPIC: str = os.getenv("KAFKA_OUTPUT_TOPIC", "ai-results")
    KAFKA_GROUP_ID: str = os.getenv("KAFKA_GROUP_ID", "multimodal-ai-group")
    MAX_IMAGE_SIZE_MB: int = int(os.getenv("MAX_IMAGE_SIZE_MB", "10"))
    MAX_AUDIO_DURATION_SECS: int = int(os.getenv("MAX_AUDIO_DURATION_SECS", "300"))
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "2048"))
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))

settings = Settings()
