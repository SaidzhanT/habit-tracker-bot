from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    telegram_bot_token: str
    supabase_url: str
    supabase_key: str

    default_reminder_time: str = "20:00"


settings = Settings()
