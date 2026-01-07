"""
Configuration management for CONCORD
"""

from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application
    APP_NAME: str = "CONCORD"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # API
    API_PREFIX: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "postgresql://concord:concord@localhost:5432/concord"
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "concord123"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # ML Models
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    SENTIMENT_MODEL: str = "cardiffnlp/twitter-roberta-base-sentiment-latest"
    
    # Consistency Thresholds
    CONSISTENCY_THRESHOLD: float = 0.7
    SIMILARITY_THRESHOLD: float = 0.85
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
