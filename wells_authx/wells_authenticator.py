"""Wells Fargo AuthX authenticator wrapper for COP Guard."""

import asyncio
from typing import Dict, Any, Optional, Tuple
from enum import Enum

from app.logging import get_logger
from .config import wells_auth_config

logger = get_logger(__name__)


class AuthProvider(Enum):
    """Authentication provider types."""
    APIGEE = "apigee"
    PINGFED = "pingfed"
    AUTO = "auto"  # Auto-detect based on token


class WellsAuthenticator:
    """Wells Fargo authentication wrapper using PyAuthenticator."""
    
    def __init__(self, provider: AuthProvider = AuthProvider.AUTO):
        """
        Initialize Wells Fargo authenticator.
        
        Args:
            provider: Authentication provider (APIGEE, PINGFED, or AUTO)
        """
        self.provider = provider
        self._apigee_authenticator = None
        self._pingfed_authenticator = None
        self._initialized = False
    
    async def _initialize_authenticators(self) -> None:
        """Initialize PyAuthenticator instances for both providers."""
        if self._initialized:
            return
        
        try:
            # Import PyAuthenticator (this will be available when wellsfargo_ebssh_python_auth is installed)
            from ebssh_python_auth.authenticate import PyAuthenticator
            
            # Initialize Apigee authenticator
            apigee_jwks_url = wells_auth_config.get_apigee_jwks_url()
            self._apigee_authenticator = PyAuthenticator(
                jwks_url=apigee_jwks_url,
                refresh='Y' if wells_auth_config.auto_refresh else 'N'
            )
            
            # Initialize PingFederate authenticator
            pingfed_jwks_url = wells_auth_config.get_pingfed_jwks_url()
            self._pingfed_authenticator = PyAuthenticator(
                jwks_url=pingfed_jwks_url,
                refresh='Y' if wells_auth_config.auto_refresh else 'N'
            )
            
            self._initialized = True
            logger.info(
                "Wells Fargo authenticators initialized",
                apigee_jwks_url=apigee_jwks_url,
                pingfed_jwks_url=pingfed_jwks_url,
                auto_refresh=wells_auth_config.auto_refresh
            )
            
        except ImportError as e:
            logger.error(
                "Failed to import PyAuthenticator. Please install wellsfargo_ebssh_python_auth",
                error=str(e)
            )
            raise RuntimeError(
                "PyAuthenticator not available. Install wellsfargo_ebssh_python_auth package."
            )
        except Exception as e:
            logger.error("Failed to initialize Wells Fargo authenticators", error=str(e))
            raise
    
    async def authenticate_token(
        self, 
        token: str, 
        client_id: Optional[str] = None
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Authenticate JWT token using Wells Fargo AuthX.
        
        Args:
            token: JWT token to authenticate
            client_id: Client ID for authentication (defaults to config)
            
        Returns:
            Tuple of (claims_dict, error_message)
        """
        try:
            await self._initialize_authenticators()
            
            # Determine which authenticator to use
            authenticator = await self._get_authenticator(token)
            if not authenticator:
                return None, "Unable to determine authentication provider"
            
            # Prepare request object
            request_obj = self._create_request_object(client_id)
            
            # Authenticate token
            result = authenticator.authenticate(token=token, request=request_obj)
            
            if result and hasattr(result, 'claims'):
                claims = result.claims
                logger.info(
                    "Token authenticated successfully",
                    provider=self.provider.value,
                    sub=claims.get('sub'),
                    client_id=claims.get('client_id'),
                    iss=claims.get('iss')
                )
                return claims, None
            else:
                error_msg = "Authentication failed: Invalid token or claims"
                logger.warning("Token authentication failed", provider=self.provider.value)
                return None, error_msg
                
        except Exception as e:
            error_msg = f"Authentication error: {str(e)}"
            logger.error("Token authentication error", error=str(e), provider=self.provider.value)
            return None, error_msg
    
    async def _get_authenticator(self, token: str):
        """Get the appropriate authenticator based on provider or token analysis."""
        if self.provider == AuthProvider.APIGEE:
            return self._apigee_authenticator
        elif self.provider == AuthProvider.PINGFED:
            return self._pingfed_authenticator
        elif self.provider == AuthProvider.AUTO:
            # Try to auto-detect based on token issuer
            try:
                # Parse token header to get issuer hint
                import jwt
                header = jwt.get_unverified_header(token)
                
                # Try Apigee first (most common)
                try:
                    result = self._apigee_authenticator.authenticate(
                        token=token, 
                        request=self._create_request_object()
                    )
                    if result and hasattr(result, 'claims'):
                        logger.debug("Auto-detected Apigee provider")
                        return self._apigee_authenticator
                except:
                    pass
                
                # Try PingFederate
                try:
                    result = self._pingfed_authenticator.authenticate(
                        token=token, 
                        request=self._create_request_object()
                    )
                    if result and hasattr(result, 'claims'):
                        logger.debug("Auto-detected PingFederate provider")
                        return self._pingfed_authenticator
                except:
                    pass
                
                # If neither works, default to Apigee
                logger.warning("Could not auto-detect provider, defaulting to Apigee")
                return self._apigee_authenticator
                
            except Exception as e:
                logger.error("Error in auto-detection", error=str(e))
                return self._apigee_authenticator
        
        return None
    
    def _create_request_object(self, client_id: Optional[str] = None):
        """Create request object for PyAuthenticator."""
        # Use provided client_id or default from config
        effective_client_id = client_id or wells_auth_config.apigee_client_id
        
        # Create a simple request object that PyAuthenticator expects
        class Request:
            def __init__(self, client_id: str):
                self.clientId = client_id
        
        return Request(effective_client_id)
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about configured providers."""
        return {
            "provider": self.provider.value,
            "apigee_jwks_url": wells_auth_config.get_apigee_jwks_url(),
            "pingfed_jwks_url": wells_auth_config.get_pingfed_jwks_url(),
            "environment": wells_auth_config.environment,
            "auto_refresh": wells_auth_config.auto_refresh,
            "initialized": self._initialized
        }


# Global Wells authenticator instance
wells_authenticator = WellsAuthenticator()


