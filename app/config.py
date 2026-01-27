"""
Configuration management
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""

    # API Keys
    openai_api_key: str
    pinecone_api_key: str

    # Pinecone settings
    pinecone_cloud: str = "aws"
    pinecone_environment: str = "us-east-1"
    pinecone_index_name: str = "conference-calls"
    pinecone_summaries_index_name: str = "conference-summaries"

    # Embedding settings
    embedding_model: str = "text-embedding-3-large"
    embedding_dimension: int = 1536

    # Metadata Database (PostgreSQL)
    database_url: str = "postgresql://user:password@localhost:5432/conference_db"
    database_echo: bool = False  # Set to True for SQL query logging

    # Agent settings
    max_iterations: int = 5
    default_top_k: int = 10
    min_relevance_score: float = 0.7

    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True

    model_config = SettingsConfigDict(
        env_file="local/.env.local",
        case_sensitive=False,
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()