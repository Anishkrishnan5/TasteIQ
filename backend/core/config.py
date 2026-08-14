from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    app_name: str = "TasteIQ"
    app_version: str = "0.2.0"
    debug: bool = True
    frontend_origin: str = "http://localhost:5173"
    rag_data_path: str | None = None


settings = Settings()
