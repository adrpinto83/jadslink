from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Configuration loaded from environment variables via .env"""

    # Environment
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://jads:jadspass@db:5432/jadslink"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # Security
    SECRET_KEY: str = "change-me-in-production"
    TICKET_HMAC_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRATION_DAYS: int = 7

    # Stripe
    STRIPE_SECRET_KEY: str = "sk_test_your_stripe_secret_key"
    STRIPE_WEBHOOK_SECRET: str = "whsec_your_stripe_webhook_secret"

    # API
    API_PREFIX: str = "/api/v1"
    API_TITLE: str = "JADSlink API"
    API_VERSION: str = "1.0"
    API_BASE_URL: str = "http://localhost:8000"  # Base URL for serving static files and redirects

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
