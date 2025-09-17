"""Configuration for Wells Fargo AuthX integration."""

from typing import List, Optional
from pydantic import BaseSettings, validator


class WellsAuthConfig(BaseSettings):
    """Configuration for Wells Fargo authentication."""
    
    # Wells Fargo AuthX settings
    apigee_jwks_url: Optional[str] = None
    pingfed_jwks_url: Optional[str] = None
    apigee_client_id: str = "EBSSH"
    pingfed_client_id: str = "EBSSH"
    
    # Environment-specific settings
    environment: str = "dev"  # dev, sit, prod
    
    # Auto-refresh settings
    auto_refresh: bool = True
    
    # Token validation settings
    validate_claims: bool = True
    validate_certificate: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        env_prefix = "WELLS_AUTH_"
    
    @validator('environment')
    def validate_environment(cls, v):
        allowed_envs = ['dev', 'sit', 'prod']
        if v not in allowed_envs:
            raise ValueError(f'Environment must be one of: {allowed_envs}')
        return v
    
    @validator('apigee_jwks_url', 'pingfed_jwks_url')
    def validate_jwks_urls(cls, v):
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
    
    def get_pingfed_jwks_url(self) -> str:
        """Get PingFederate JWKS URL based on environment."""
        if self.pingfed_jwks_url:
            return self.pingfed_jwks_url
        
        # Default URLs based on environment
        urls = {
            'dev': 'https://cspf-dev.wellsfargo.net/pf/JWKS',
            'sit': 'https://cspf-sit.wellsfargo.net/pf/JWKS',
            'prod': 'https://cspf-prod.wellsfargo.net/pf/JWKS'
        }
        return urls.get(self.environment, urls['dev'])


# Global Wells Auth configuration
wells_auth_config = WellsAuthConfig()


