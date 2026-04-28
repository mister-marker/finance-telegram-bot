from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr


class Settings(BaseSettings):
    BOT_TOKEN: SecretStr
    DATABASE_URL: str

    WEBHOOK_PATH: str = "/webhook"
    BASE_WEBHOOK_URL: str = ""

   
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )


settings = Settings()