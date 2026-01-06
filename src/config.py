"""Configuration management using pydantic-settings"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Database
    database_url: str

    # Collection settings
    collection_interval_seconds: int = 60  # 1 minute
    batch_size: int = 100
    max_concurrent_requests: int = 10

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
