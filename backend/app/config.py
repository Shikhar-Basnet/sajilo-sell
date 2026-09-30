from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def APP_DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.APP_DB_USER}:{self.APP_DB_PASSWORD}"
            f"@{self.APP_DB_HOST}:{self.APP_DB_PORT}/{self.APP_DB_NAME}"
        )


settings = Settings()