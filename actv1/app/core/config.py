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
    cors_origins: str = ""

    database_url: str = "postgresql+psycopg://precursa:precursa@localhost:5432/precursa"
    redis_url: str = ""  # Empty = use in-memory fallback
    state_cache_key_prefix: str = "shipment_state"
    state_cache_ttl_seconds: int = 3600
    agent_tick_seconds: int = 30
    agent_autostart: bool = True
    mvp_mode: bool = True
    agent_reroute_threshold: int = 75
    dri_threshold_yellow: int = 31
    dri_threshold_orange: int = 61
    dri_threshold_red: int = 81
    wargame_tick_seconds: int = 10
    wargame_disturber_intensity: float = 0.7
    kafka_bootstrap_servers: str = ""
    notification_default_recipient: str = "ops-control@precursa.local"

    # External Integration Keys
    tomorrow_io_api_key: str | None = None
    aisstream_api_key: str | None = None
    news_api_key: str | None = None

    # Copilot LLM settings
    copilot_llm_provider: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b"
    ollama_timeout_seconds: int = 30

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

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
