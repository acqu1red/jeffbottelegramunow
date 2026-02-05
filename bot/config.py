from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    bot_token: str
    bot_username: str
    admin_channel_id: int
    admin1_id: int | None = None
    admin2_id: int | None = None
    admin3_id: int | None = None
    admin4_id: int | None = None
    fernet_key: str
    database_url: str
    webhook_base_url: str
    tinkoff_terminal_key: str
    tinkoff_secret: str
    admin_password_hash: str
    admin_password_salt: str
    app_secret: str

    @property
    def admin_ids(self) -> list[int]:
        ids = [self.admin1_id, self.admin2_id, self.admin3_id, self.admin4_id]
        return [i for i in ids if i is not None]


@lru_cache
def get_settings() -> Settings:
    return Settings()
