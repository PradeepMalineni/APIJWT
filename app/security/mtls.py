"""TLS support for secure connections."""

import ssl
from typing import Optional, Dict, Any

from fastapi import Request, HTTPException, status

from app.config import settings
from app.logging import get_logger

logger = get_logger(__name__)


class TLSValidationError(Exception):
    """Custom exception for TLS validation errors."""
    pass


class TLSValidator:
    """TLS validator for secure connections."""
    
    def __init__(self):
        self.enabled = settings.tls_enabled
    
    async def validate_tls_connection(self, request: Request) -> Optional[Dict[str, Any]]:
        """
        Validate TLS connection information.
        
        Args:
            request: FastAPI request object
            
        Returns:
            TLS connection information dict or None if TLS not enabled
            
        Raises:
            HTTPException: If TLS is required but connection is not secure
        """
        if not self.enabled:
            return None
        
        try:
            # Check if connection is secure (HTTPS)
            is_secure = request.url.scheme == 'https'
            
            if not is_secure:
                logger.warning("TLS required but connection is not secure")
                raise HTTPException(
                    status_code=status.HTTP_426_UPGRADE_REQUIRED,
                    detail={
                        "code": "426",
                        "status": "tls_error",
                        "error_message": "HTTPS connection required"
                    }
                )
            
            # Get TLS connection info
            tls_info = self._get_tls_info(request)
            
            logger.info(
                "TLS connection validated",
                scheme=request.url.scheme,
                host=request.url.hostname,
                port=request.url.port
            )
            
            return tls_info
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("TLS validation error", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "code": "500",
                    "status": "tls_error",
                    "error_message": f"TLS validation failed: {str(e)}"
                }
            )
    
    def _get_tls_info(self, request: Request) -> Dict[str, Any]:
        """Extract TLS connection information."""
        return {
            'scheme': request.url.scheme,
            'hostname': request.url.hostname,
            'port': request.url.port,
            'is_secure': request.url.scheme == 'https',
            'protocol': 'TLS 1.3' if request.url.scheme == 'https' else 'HTTP'
        }
    
    def get_tls_scheme(self, tls_info: Optional[Dict[str, Any]]) -> Optional[str]:
        """Get TLS scheme from connection info."""
        if not tls_info:
            return None
        return tls_info.get('scheme')
    
    def get_tls_protocol(self, tls_info: Optional[Dict[str, Any]]) -> Optional[str]:
        """Get TLS protocol from connection info."""
        if not tls_info:
            return None
        return tls_info.get('protocol')


# Global TLS validator instance
tls_validator = TLSValidator()
