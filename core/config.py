from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/sezi"
    ntfy_url: str = "https://ntfy.sh"
    ntfy_topic: str = ""
    ntfy_token: str = ""  # boş bırakılırsa auth olmadan gönderir
    app_env: str = "development"
    log_level: str = "INFO"

    @property
    def is_dev(self) -> bool:
        return self.app_env == "development"


settings = Settings()
