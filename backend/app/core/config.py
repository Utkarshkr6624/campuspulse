from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.document_enums import DEFAULT_MAX_UPLOAD_BYTES

_JWT_SECRET_PLACEHOLDER = "replace-this-with-a-random-string-at-least-32-characters"

BACKEND_DIR = Path(__file__).resolve().parents[2]


def resolve_database_url(url: str) -> str:
    prefix = "sqlite:///"
    if not url.startswith(prefix) or url == "sqlite:///:memory:":
        return url

    raw_path = url[len(prefix) :]
    path = Path(raw_path)
    if not path.is_absolute():
        path = BACKEND_DIR / path
    return prefix + path.resolve().as_posix()


class Settings(BaseSettings):
    app_name: str = "CampusPulse"
    database_url: str = "sqlite:///./campuspulse.db"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    jwt_secret_key: str
    jwt_expire_minutes: int = 120
    document_storage_backend: str = "local"
    document_storage_path: str = "./storage/uploads"
    document_max_upload_bytes: int = DEFAULT_MAX_UPLOAD_BYTES
    ai_provider: str = "deterministic"
    ai_model: str = "rules"
    ai_base_url: str = ""
    ai_api_key: str | None = None
    ai_timeout_seconds: int = 30
    ai_max_history_messages: int = 10

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret(cls, value: str) -> str:
        secret = value.strip()
        if len(secret) < 32 or secret == _JWT_SECRET_PLACEHOLDER:
            raise ValueError("Set JWT_SECRET_KEY to a random string of at least 32 characters.")
        return secret

    @field_validator("jwt_expire_minutes")
    @classmethod
    def validate_jwt_expiry(cls, value: int) -> int:
        if value < 5 or value > 1440:
            raise ValueError("JWT_EXPIRE_MINUTES must be between 5 and 1440.")
        return value

    @field_validator("document_max_upload_bytes")
    @classmethod
    def validate_upload_limit(cls, value: int) -> int:
        if value < 1024 or value > 50 * 1024 * 1024:
            raise ValueError("DOCUMENT_MAX_UPLOAD_BYTES must be between 1 KiB and 50 MiB.")
        return value

    @field_validator("ai_timeout_seconds")
    @classmethod
    def validate_ai_timeout(cls, value: int) -> int:
        if value < 5 or value > 120:
            raise ValueError("AI_TIMEOUT_SECONDS must be between 5 and 120.")
        return value

    @field_validator("ai_max_history_messages")
    @classmethod
    def validate_history(cls, value: int) -> int:
        if value < 2 or value > 40:
            raise ValueError("AI_MAX_HISTORY_MESSAGES must be between 2 and 40.")
        return value

    @property
    def resolved_database_url(self) -> str:
        return resolve_database_url(self.database_url)

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
