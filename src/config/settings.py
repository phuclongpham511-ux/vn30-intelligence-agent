from functools import lru_cache
from pathlib import Path
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=PROJECT_ROOT / ".env", extra="ignore")
    database_url: str = "sqlite:///./vn30.db"
    openai_api_key: SecretStr = SecretStr("")
    app_env: str = "development"
    market_data_provider: str = "ssi"
    ssi_api_key: SecretStr = SecretStr("")
    ssi_api_secret: SecretStr = SecretStr("")


@lru_cache
def get_settings() -> Settings:
    return Settings()
