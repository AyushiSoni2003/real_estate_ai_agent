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
    OPENAI_API_KEY: Optional[str] = None
    
    # Security
    SECRET_KEY: str = "your-super-secret-key-change-this-in-production"
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"  # Load from .env file
        case_sensitive = True  # Environment variables are case-sensitive


# Create global settings instance
settings = Settings()
