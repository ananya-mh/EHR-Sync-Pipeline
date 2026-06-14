"""Centralized application settings loaded from environment variables.

All configuration for the EHR-Sync-Pipeline lives here. Access settings
through the module-level ``settings`` singleton — never use ``os.getenv()``
directly.  Environment variables are prefixed with ``EHR_`` (e.g.
``EHR_DB_HOST``).
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings validated at startup via pydantic-settings."""

    # -- Database --
    db_host: str = "postgres"
    db_port: int = 5432
    db_name: str = "ehr_db"
    db_user: str = "postgres"
    db_password: str = "password"
    db_pool_min_size: int = 2
    db_pool_max_size: int = 10
    db_pool_max_idle: float = 300.0

    # -- Kafka --
    kafka_bootstrap_servers: str = "kafka:9092"
    kafka_consumer_group_prefix: str = "ehr-pipeline"
    kafka_dlq_topic: str = "ehr.dlq"
    kafka_max_retries: int = 3

    # -- API --
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # -- Logging --
    log_level: str = "INFO"
    log_format: str = "json"

    model_config = {"env_prefix": "EHR_"}


settings = Settings()
