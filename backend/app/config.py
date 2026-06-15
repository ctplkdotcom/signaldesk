from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Signal Desk"
    app_version: str = "0.2.0"
    debug: bool = False
    log_level: str = "INFO"
    secret_key: str = "change-me-in-production"
    cors_origins: str = "http://localhost:3000"

    # Database mode: "sqlite" (default) or "postgresql"
    database_mode: str = "sqlite"
    sqlite_path: str = "signal_desk.db"

    # PostgreSQL (optional advanced mode)
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "signal_desk"
    postgres_user: str = "signal_desk"
    postgres_password: str = "change-me"

    @property
    def database_url(self) -> str:
        if self.database_mode == "sqlite":
            return f"sqlite+aiosqlite:///{self.sqlite_path}"
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @property
    def database_url_sync(self) -> str:
        if self.database_mode == "sqlite":
            return f"sqlite:///{self.sqlite_path}"
        return f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    # Provider: Polygon.io (primary)
    polygon_api_key: str = ""

    # Cache TTL
    cache_ttl_price: int = 60
    cache_ttl_ticker: int = 3600

    # TimescaleDB
    use_timescaledb: bool = False

    # Workers
    request_timeout: int = 30
    min_data_points: int = 252

    # Data retention (days)
    retention_days: int = 120

    # Initial backfill (months)
    backfill_months: int = 3
    backfill_max_months: int = 4

    # Auto-refresh interval (seconds)
    auto_refresh_interval: int = 60


settings = Settings()
