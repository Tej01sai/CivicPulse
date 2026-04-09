"""Application configuration from environment variables."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from .env file."""

    # Database
    database_url: str

    # Anthropic
    anthropic_api_key: str

    # Pinecone
    pinecone_api_key: str
    pinecone_index_name: str = "smartresource-needs"
    pinecone_environment: str = "us-east-1-aws"

    # Twilio
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_from_number: str
    coordinator_phone: str

    # Auth0
    auth0_domain: str
    auth0_audience: str
    auth0_client_id: str

    # App
    app_url: str = "http://localhost:5173"
    backend_url: str = "http://localhost:8000"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
