from functools import lru_cache
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "sqlite:///./vn30.db"
    openai_api_key: SecretStr = SecretStr("")
    app_env: str = "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
