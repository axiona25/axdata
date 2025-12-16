"""Configuration settings using Pydantic Settings."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Environment
    environment: str = "development"
    
    # Database
    database_url: str
    
    # Redis
    redis_url: str
    
    # Object Storage (S3-compatible)
    s3_endpoint_url: Optional[str] = None
    s3_access_key_id: str
    s3_secret_access_key: str
    s3_bucket: str
    s3_region: str = "us-east-1"
    
    # OpenAI
    openai_api_key: str = ""  # Will be loaded from API_KEYS.md or env (required)
    openai_model: str = "gpt-4-turbo-preview"
    
    # Stripe
    stripe_secret_key: Optional[str] = None
    stripe_publishable_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    
    # PayPal
    paypal_client_id: Optional[str] = None
    paypal_client_secret: Optional[str] = None
    paypal_webhook_id: Optional[str] = None
    
    # Email (SendGrid SMTP)
    email_enabled: bool = True
    email_smtp_host: str = "smtp.sendgrid.net"
    email_smtp_port: int = 587
    email_smtp_user: str = "apikey"  # Fixed for SendGrid
    email_smtp_password: Optional[str] = None  # SendGrid API Key
    email_use_tls: bool = True
    email_from: str = "no-reply@axdata.eu"  # Indirizzo "from" verificato su SendGrid (NON l'email dell'utente!)
    
    def __init__(self, **kwargs):
        """Initialize settings with API keys from API_KEYS.md if available."""
        # First, try to load from API_KEYS.md before loading from env
        from core.api_keys import (
            get_openai_api_key,
            get_stripe_secret_key,
            get_stripe_publishable_key,
            get_stripe_webhook_secret,
            get_paypal_client_id,
            get_paypal_client_secret,
            get_paypal_webhook_id,
            get_sendgrid_api_key
        )
        
        # Override kwargs with API_KEYS.md values if available (priority)
        if "openai_api_key" not in kwargs or not kwargs.get("openai_api_key") or kwargs.get("openai_api_key") == "sk-placeholder":
            api_key = get_openai_api_key()
            if api_key:
                kwargs["openai_api_key"] = api_key
        
        if "stripe_secret_key" not in kwargs or not kwargs.get("stripe_secret_key"):
            stripe_key = get_stripe_secret_key()
            if stripe_key:
                kwargs["stripe_secret_key"] = stripe_key
        
        if "stripe_publishable_key" not in kwargs or not kwargs.get("stripe_publishable_key"):
            stripe_pub = get_stripe_publishable_key()
            if stripe_pub:
                kwargs["stripe_publishable_key"] = stripe_pub
        
        if "stripe_webhook_secret" not in kwargs or not kwargs.get("stripe_webhook_secret"):
            stripe_wh = get_stripe_webhook_secret()
            if stripe_wh:
                kwargs["stripe_webhook_secret"] = stripe_wh
        
        # PayPal keys
        if "paypal_client_id" not in kwargs or not kwargs.get("paypal_client_id"):
            paypal_id = get_paypal_client_id()
            if paypal_id:
                kwargs["paypal_client_id"] = paypal_id
        
        if "paypal_client_secret" not in kwargs or not kwargs.get("paypal_client_secret"):
            paypal_secret = get_paypal_client_secret()
            if paypal_secret:
                kwargs["paypal_client_secret"] = paypal_secret
        
        if "paypal_webhook_id" not in kwargs or not kwargs.get("paypal_webhook_id"):
            paypal_wh = get_paypal_webhook_id()
            if paypal_wh:
                kwargs["paypal_webhook_id"] = paypal_wh
        
        # SendGrid email key
        if "email_smtp_password" not in kwargs or not kwargs.get("email_smtp_password"):
            sendgrid_key = get_sendgrid_api_key()
            if sendgrid_key:
                kwargs["email_smtp_password"] = sendgrid_key
        
        super().__init__(**kwargs)
    
    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:3000"
    
    # Celery
    celery_broker_url: Optional[str] = None
    celery_result_backend: Optional[str] = None
    
    # Signed URLs
    signed_url_ttl: int = 3600
    
    # GDPR / Purge
    user_purge_retention_days: int = 30  # Days to retain deleted user data
    
    # Logging
    log_level: str = "INFO"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
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

