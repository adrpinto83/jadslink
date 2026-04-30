from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Configuration loaded from environment variables via .env"""

    # Environment
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Database (MySQL/MariaDB for Hostinger compatibility)
    DATABASE_URL: str = "mysql+aiomysql://user:password@localhost:3306/jadslink"

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

    # Email / Resend
    RESEND_API_KEY: str = ""  # Leave empty to disable email sending
    EMAIL_FROM: str = "noreply@jadslink.io"
    EMAIL_FROM_NAME: str = "JADSlink"
    SUPPORT_EMAIL: str = "support@jadslink.io"

    # API
    API_PREFIX: str = "/api/v1"
    API_TITLE: str = "JADSlink API"
    API_VERSION: str = "1.0"
    API_BASE_URL: str = "http://localhost:8000"  # Base URL for serving static files and redirects
    FRONTEND_URL: str = "http://localhost:3000"  # Frontend URL for CORS and redirects

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
