from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    ENVIRONMENT: str = "development"

    # Admin/migration connection — table owner, used ONLY by Alembic (see alembic/env.py).
    # Never used to serve API requests, since this role bypasses Row-Level Security.
    DATABASE_URL: str

    # Least-privilege runtime connection — this is what FastAPI actually
    # connects as for every request. RLS policies are enforced against it.
    APP_DB_USER: str = "sajilo_app"
    APP_DB_PASSWORD: str
    APP_DB_HOST: str = "postgres"
    APP_DB_PORT: int = 5432
    APP_DB_NAME: str = "sajilo_sell"

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    @property
    def APP_DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.APP_DB_USER}:{self.APP_DB_PASSWORD}"
            f"@{self.APP_DB_HOST}:{self.APP_DB_PORT}/{self.APP_DB_NAME}"
        )


settings = Settings()