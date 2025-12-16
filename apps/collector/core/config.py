"""Configuration settings for Collector Service."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Collector service settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Environment
    environment: str = "development"
    
    # Object Storage (S3-compatible)
    s3_endpoint_url: Optional[str] = None
    s3_access_key_id: str
    s3_secret_access_key: str
    s3_bucket: str
    s3_region: str = "us-east-1"
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8001
    
    # Logging
    log_level: str = "INFO"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment.lower() == "development"


# Global settings instance
settings = Settings()

