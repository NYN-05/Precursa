from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    project_name: str = "Precursa Platform Foundation"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"

    database_url: str = "postgresql+psycopg://precursa:precursa@localhost:5432/precursa"
    redis_url: str = "redis://localhost:6379/0"
    state_cache_key_prefix: str = "shipment_state"
    state_cache_ttl_seconds: int = 3600

    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    default_admin_username: str = "admin"
    default_admin_password: str = "admin123"
    seed_on_startup: bool = True

    allowed_roles: tuple[str, ...] = (
        "admin",
        "ops_analyst",
        "logistics_manager",
        "auditor",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
