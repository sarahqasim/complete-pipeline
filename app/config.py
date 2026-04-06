import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # API Keys
    ANTHROPIC_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: Optional[str] = None

    # LLM routing
    LLM_PROVIDER: str = "auto"
    LLM_FALLBACK_PROVIDER: Optional[str] = None
    TEXT_MODEL: str = "gemini-2.5-flash"
    FALLBACK_TEXT_MODEL: Optional[str] = None
    VISION_MODEL: str = "gemini-2.5-flash"
    LLM_MAX_RETRIES: int = 2
    LLM_RETRY_DELAY_SECONDS: float = 1.5

    # Database
    DATABASE_URL: str = "sqlite:///./app.db"

    # File storage
    UPLOAD_DIR: str = "uploads"
    OUTPUT_DIR: str = "outputs"
    POPPLER_PATH: str = r"C:\Program Files\poppler\Library\bin"

    # Extraction
    DPI_FOR_VISION: int = 200

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
