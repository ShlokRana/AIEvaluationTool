from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class Settings(BaseSettings):
    SECRET_KEY: str = os.getenv("AUTH_SECRET_KEY", "@cerai")
    REFRESH_SECRET_KEY: str = os.getenv("AUTH_REFRESH_SECRET_KEY", "@cerai_refresh")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 512
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database settings
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "aievaluation")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()