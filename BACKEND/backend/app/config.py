import os
from pathlib import Path
from typing import List, Union
from dotenv import load_dotenv

# Project root directory and absolute .env path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_FILE_PATH = str(PROJECT_ROOT / ".env")

# Pre-load .env into os.environ if it exists
if os.path.exists(ENV_FILE_PATH):
    load_dotenv(dotenv_path=ENV_FILE_PATH, override=False)

try:
    from pydantic import field_validator
    from pydantic_settings import BaseSettings, SettingsConfigDict

    class Settings(BaseSettings):
        # App Settings
        APP_NAME: str = "Space Explorer API"
        APP_VERSION: str = "0.1.0"
        APP_ENV: str = "development"
        DEBUG: bool = True
        API_V1_PREFIX: str = "/api/v1"
        HOST: str = "0.0.0.0"
        PORT: int = 8000

        # Security
        SECRET_KEY: str = "insecure-default-development-secret-key"

        # Database Settings (Defaults to SQLite for local development; switchable to PostgreSQL + PostGIS)
        DATABASE_URL: str = "sqlite:///./space_explorer.db"

        # CORS Settings
        CORS_ORIGINS: Union[str, List[str]] = [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]

        # LLM Provider Configuration (SRS Section 16 & Plan Section 9)
        LLM_PROVIDER: str = "none"
        GROQ_API_KEY: str = ""
        GROQ_MODEL: str = ""
        GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
        LLM_TIMEOUT_SECONDS: float = 15.0

        @field_validator("CORS_ORIGINS", mode="before")
        @classmethod
        def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
            if isinstance(v, str) and not v.startswith("["):
                return [i.strip().rstrip("/") for i in v.split(",") if i.strip()]
            elif isinstance(v, list):
                return [i.strip().rstrip("/") for i in v if isinstance(i, str) and i.strip()]
            return []

        model_config = SettingsConfigDict(
            env_file=ENV_FILE_PATH if os.path.exists(ENV_FILE_PATH) else ".env",
            env_file_encoding="utf-8",
            case_sensitive=True,
            extra="ignore",
        )

    settings = Settings()

except ImportError:
    # Resilient fallback if pydantic_settings is not yet installed in local python environment
    class FallbackSettings:
        def __init__(self):
            self.APP_NAME: str = os.getenv("APP_NAME", "Space Explorer API")
            self.APP_VERSION: str = os.getenv("APP_VERSION", "0.1.0")
            self.APP_ENV: str = os.getenv("APP_ENV", "development")
            self.DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1")
            self.API_V1_PREFIX: str = os.getenv("API_V1_PREFIX", "/api/v1")
            self.HOST: str = os.getenv("HOST", "0.0.0.0")
            self.PORT: int = int(os.getenv("PORT", 8000))
            self.SECRET_KEY: str = os.getenv("SECRET_KEY", "insecure-default-development-secret-key")
            self.DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./space_explorer.db")

            raw_cors = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173")
            if isinstance(raw_cors, str):
                self.CORS_ORIGINS: List[str] = [i.strip().rstrip("/") for i in raw_cors.split(",") if i.strip()]
            else:
                self.CORS_ORIGINS: List[str] = [i.strip().rstrip("/") for i in raw_cors if isinstance(i, str) and i.strip()]

            self.LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "none")
            self.GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
            self.GROQ_MODEL: str = os.getenv("GROQ_MODEL", "")
            self.GROQ_BASE_URL: str = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
            self.LLM_TIMEOUT_SECONDS: float = float(os.getenv("LLM_TIMEOUT_SECONDS", "15.0"))

    settings = FallbackSettings()
