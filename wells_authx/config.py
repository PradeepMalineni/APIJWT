"""Configuration for Wells Fargo AuthX integration - Apigee Only."""

from typing import Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings


class WellsAuthConfig(BaseSettings):
    """Configuration for Wells Fargo authentication - Apigee only."""
    
    # Wells Fargo AuthX settings
    apigee_jwks_url: Optional[str] = None
    apigee_client_id: str = "EBSSH"
    
    # Environment-specific settings
    environment: str = "dev"  # dev, sit, prod
    
    # Auto-refresh settings
    auto_refresh: bool = True
    
    # Token validation settings
    validate_claims: bool = True
    validate_certificate: bool = True
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "env_prefix": "WELLS_AUTH_"
    }
    
    @field_validator('environment')
    @classmethod
    def validate_environment(cls, v):
        allowed_envs = ['dev', 'sit', 'prod']
        if v not in allowed_envs:
            raise ValueError(f'Environment must be one of: {allowed_envs}')
        return v
    
    @field_validator('apigee_jwks_url')
    @classmethod
    def validate_jwks_url(cls, v):
        if v and not v.startswith('https://'):
            raise ValueError('JWKS URLs must use HTTPS')
        return v
    
    def get_apigee_jwks_url(self) -> str:
        """Get Apigee JWKS URL based on environment."""
        if self.apigee_jwks_url:
            return self.apigee_jwks_url
        
        # Default URLs based on environment
        urls = {
            'dev': 'https://jwks-service-dev.cfapps.wellsfargo.net/publickey/getKeys',
            'sit': 'https://jwks-service-sit.cfapps.wellsfargo.net/publickey/getKeys',
            'prod': 'https://jwks-service-prod.cfapps.wellsfargo.net/publickey/getKeys'
        }
        return urls.get(self.environment, urls['dev'])


# Global Wells Auth configuration
wells_auth_config = WellsAuthConfig()