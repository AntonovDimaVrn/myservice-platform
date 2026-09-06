from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://myservice:myservice@postgres:5432/myservice"
    rabbitmq_url: str = "amqp://myservice:myservice@rabbitmq:5672/"
    outbox_poll_interval: float = 1.0
    outbox_batch_size: int = 50
    rabbitmq_exchange: str = "orders.events"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
