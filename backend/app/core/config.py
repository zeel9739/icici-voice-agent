from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ────────────────────────────────────────────────────────────
    APP_NAME: str = "ICICI Prudential Voice Agent"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # ── Database ───────────────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./icici_leads.db"

    # ── LiveKit ────────────────────────────────────────────────────────────────
    LIVEKIT_URL: str
    LIVEKIT_API_KEY: str
    LIVEKIT_API_SECRET: str

    # ── STT / LLM / TTS providers ──────────────────────────────────────────────
    DEEPGRAM_API_KEY: str
    GROQ_API_KEY: str
    CARTESIA_API_KEY: str

    # ── Agent tuning ───────────────────────────────────────────────────────────
    # Minimum word count to forward a transcript to the LLM (noise filter)
    MIN_TRANSCRIPT_WORDS: int = 2
    # Minimum Deepgram confidence score [0.0 – 1.0] to accept a transcript
    MIN_TRANSCRIPT_CONFIDENCE: float = 0.65
    # Groq model to use
    LLM_MODEL: str = "llama3-8b-8192"
    CARTESIA_VOICE_ID: str = "79a125e8-cd45-4c13-8a67-188112f4dd22"  # British lady


@lru_cache
def get_settings() -> Settings:
    return Settings()
