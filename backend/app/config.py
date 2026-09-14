from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="")

    database_url: str = "postgresql+psycopg://crm:local-development-only@db:5432/crm"
    data_dir: Path = Path("/app/data")


settings = Settings()
