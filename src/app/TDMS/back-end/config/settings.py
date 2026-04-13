from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class Settings(BaseSettings):
    SECRET_KEY: str = os.getenv("AUTH_SECRET_KEY", "@cerai")
    REFRESH_SECRET_KEY: str = os.getenv("AUTH_REFRESH_SECRET_KEY", "@cerai_refresh")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    BASE_URL: str = "http://localhost:8000"

    # Auth Service URL
    AUTH_SERVICE_URL: str = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()