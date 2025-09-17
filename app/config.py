"""Configuration management for COP Guard API protection layer."""

import os
from typing import List, Optional
from pydantic import BaseSettings, validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Server configuration
    port: int = 8080
    host: str = "0.0.0.0"
    
    # JWT/Auth configuration
    cop_audience: str = "TSIAM"
    allowed_issuers: List[str] = []
    jwks_url_primary: Optional[str] = None
    jwks_url_secondary: Optional[str] = None
    jwks_cache_ttl_sec: int = 900
    jwks_background_refresh_sec: int = 600
    max_clock_skew_sec: int = 120
    
    # TLS configuration
    tls_enabled: bool = True
    
    # Rate limiting
    rate_limit_default_per_min: int = 100
    
    # Logging
    log_level: str = "INFO"
    
    # Metrics
    enable_metrics: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        
    @validator('allowed_issuers', pre=True)
    def parse_allowed_issuers(cls, v):
        if isinstance(v, str):
            return [issuer.strip() for issuer in v.split(',') if issuer.strip()]
        return v
    
    @validator('jwks_url_primary', 'jwks_url_secondary')
    def validate_jwks_urls(cls, v):
        if v and not v.startswith('https://'):
            raise ValueError('JWKS URLs must use HTTPS')
        return v


# Global settings instance
settings = Settings()
