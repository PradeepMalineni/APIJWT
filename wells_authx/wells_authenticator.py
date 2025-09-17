"""Wells Fargo AuthX authenticator wrapper for COP Guard - Apigee Only."""

import asyncio
import logging
from typing import Dict, Any, Optional, Tuple

from config import wells_auth_config

logger = logging.getLogger(__name__)


class WellsAuthenticator:
    """Wells Fargo authentication wrapper using PyAuthenticator for Apigee only."""
    
    def __init__(self):
        """Initialize Wells Fargo authenticator for Apigee."""
        self._apigee_authenticator = None
        self._initialized = False
    
    async def _initialize_authenticator(self) -> None:
        """Initialize PyAuthenticator instance for Apigee."""
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
            
            self._initialized = True
            logger.info(
                "Wells Fargo Apigee authenticator initialized",
                extra={
                    "apigee_jwks_url": apigee_jwks_url,
                    "auto_refresh": wells_auth_config.auto_refresh
                }
            )
            
        except ImportError as e:
            logger.error(
                "Failed to import PyAuthenticator. Please install wellsfargo_ebssh_python_auth",
                extra={"error": str(e)}
            )
            raise RuntimeError(
                "PyAuthenticator not available. Install wellsfargo_ebssh_python_auth package."
            )
        except Exception as e:
            logger.error("Failed to initialize Wells Fargo authenticator", extra={"error": str(e)})
            raise
    
    async def authenticate_token(
        self, 
        token: str, 
        client_id: Optional[str] = None
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Authenticate JWT token using Wells Fargo AuthX Apigee.
        
        Args:
            token: JWT token to authenticate
            client_id: Client ID for authentication (defaults to config)
            
        Returns:
            Tuple of (claims_dict, error_message)
        """
        try:
            await self._initialize_authenticator()
            
            # Prepare request object
            request_obj = self._create_request_object(client_id)
            
            # Authenticate token using Apigee
            result = self._apigee_authenticator.authenticate(token=token, request=request_obj)
            
            if result and hasattr(result, 'claims'):
                claims = result.claims
                logger.info(
                    "Token authenticated successfully via Apigee",
                    extra={
                        "sub": claims.get('sub'),
                        "client_id": claims.get('client_id'),
                        "iss": claims.get('iss')
                    }
                )
                return claims, None
            else:
                error_msg = "Authentication failed: Invalid token or claims"
                logger.warning("Token authentication failed via Apigee")
                return None, error_msg
                
        except Exception as e:
            error_msg = f"Authentication error: {str(e)}"
            logger.error("Token authentication error via Apigee", extra={"error": str(e)})
            return None, error_msg
    
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
        """Get information about configured Apigee provider."""
        return {
            "provider": "apigee",
            "apigee_jwks_url": wells_auth_config.get_apigee_jwks_url(),
            "environment": wells_auth_config.environment,
            "auto_refresh": wells_auth_config.auto_refresh,
            "initialized": self._initialized
        }


# Global Wells authenticator instance
wells_authenticator = WellsAuthenticator()