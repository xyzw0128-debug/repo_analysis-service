from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    github_token: str
    llm_provider: str
    llm_model: str
    llm_api_key: str
    database_url: str = "sqlite:///./repoforge.db"
    max_input_tokens: int = 24000
    max_concurrent_jobs: int = 5

    model_config = SettingsConfigDict(env_file=".env")


@lru_cache
def get_settings() -> Settings:
    return Settings()
