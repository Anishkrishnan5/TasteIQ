from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    app_name: str = "TasteIQ"
    app_version: str = "0.3.0"
    frontend_origin: str = "http://localhost:5173"
    rag_data_path: str | None = None
    retrieval_mode: Literal["bm25", "hybrid"] = "bm25"
    database_url: str = "postgresql+psycopg://tasteiq:tasteiq@localhost:5432/tasteiq"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.6-flash"
    llm_timeout_seconds: float = 20


settings = Settings()
