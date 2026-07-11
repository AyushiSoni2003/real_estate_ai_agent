"""Application configuration and environment settings."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Why use Pydantic Settings?
    - Type validation: Ensures all env vars are correct type
    - Defaults: Provides sensible defaults for optional settings
    - .env support: Reads from .env file automatically
    - Documentation: Settings are self-documenting
    
    Environment Variables (.env file):
    - APP_NAME: Application name for FastAPI docs
    - DEBUG: Enable debug mode (development only)
    - DATABASE_URL: PostgreSQL connection string (async driver)
    - REDIS_URL: Redis connection string (caching, sessions)
    - QDRANT_URL: Qdrant vector database URL (for AI embeddings)
    - OPENAI_API_KEY: OpenAI API key for AI features
    - SECRET_KEY: JWT signing secret (CHANGE IN PRODUCTION)
    """
    
    # Application Settings
    APP_NAME: str = "RealtyIQ"
    DEBUG: bool = False
    
    # Database Settings
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/realtyiq_db"
    
    # Cache & Vector DB
    REDIS_URL: str = "redis://localhost:6379"
    QDRANT_URL: str = "http://localhost:6333"
    
    # External APIs
    GOOGLE_API_KEY: str = ""
    
   # JWT Settings  
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # Twilio Settings
    # I will have to change twilio with whatsapp API settings in the future
    # TWILIO_ACCOUNT_SID: str = ""
    # TWILIO_AUTH_TOKEN: str = ""
    # TWILIO_WHATSAPP_FROM: str = "whatsapp:+14155238886"

    # Email Settings
    # Will have to change email settings with SMTP settings in the future
    # SENDGRID_API_KEY: str = ""
    # SENDGRID_FROM_EMAIL: str = "no-reply@realtyiq.com"

    # Security
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION"  # Change this in production for security
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"  # Load from .env file
        case_sensitive = True  # Environment variables are case-sensitive


# Create global settings instance
settings = Settings()
