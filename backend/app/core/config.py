from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5433/injuryrisk"
    SECRET_KEY: str = "dev-secret-change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    CORS_ORIGINS: str = "http://localhost:5173"
    # Pasta com o build do React (npm run build). Quando existe, a API também
    # serve o frontend — é assim que roda no Docker e no deploy.
    STATIC_DIR: str = "static"

    @field_validator("DATABASE_URL")
    @classmethod
    def usar_driver_psycopg(cls, url: str) -> str:
        """Aceita a URL como os provedores entregam (Neon, Render, Heroku).

        Eles fornecem `postgres://` ou `postgresql://`; o SQLAlchemy precisa do
        prefixo `postgresql+psycopg://` para usar o driver psycopg 3.
        """
        for prefixo in ("postgres://", "postgresql://"):
            if url.startswith(prefixo):
                return "postgresql+psycopg://" + url[len(prefixo):]
        return url

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def static_path(self) -> Path:
        return Path(self.STATIC_DIR).resolve()


settings = Settings()
