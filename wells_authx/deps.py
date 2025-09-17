"""FastAPI dependencies for Wells Fargo AuthX integration."""

from typing import Optional, Dict, Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.logging import get_logger
from app.security.mtls import tls_validator
from .wells_authenticator import wells_authenticator, AuthProvider

logger = get_logger(__name__)

# HTTP Bearer token security scheme
security = HTTPBearer(auto_error=False)


async def get_wells_authenticated_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    provider: AuthProvider = AuthProvider.AUTO
) -> Dict[str, Any]:
    """
    FastAPI dependency to authenticate using Wells Fargo AuthX.
    
    Args:
        request: FastAPI request object
        credentials: HTTP Bearer credentials
        provider: Authentication provider to use
        
    Returns:
        JWT claims dictionary
        
    Raises:
        HTTPException: If authentication fails
    """
    # Validate TLS connection if required
    tls_info = await tls_validator.validate_tls_connection(request)
    
    # Extract JWT token
    if not credentials:
        logger.warning("No authorization header provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "401",
                "status": "auth_error",
                "error_message": "Authorization header required"
            }
        )
    
    token = credentials.credentials
    
    # Authenticate using Wells Fargo AuthX
    claims, error = await wells_authenticator.authenticate_token(token)
    
    if error:
        logger.warning("Wells Fargo authentication failed", error=error, provider=provider.value)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "401",
                "status": "auth_error",
                "error_message": error
            }
        )
    
    # Store claims in request state for use by other dependencies
    request.state.claims = claims
    request.state.tls_info = tls_info
    request.state.auth_provider = provider.value
    
    # Log successful authentication
    logger.info(
        "User authenticated successfully via Wells Fargo AuthX",
        sub=claims.get('sub'),
        client_id=claims.get('client_id'),
        iss=claims.get('iss'),
        aud=claims.get('aud'),
        scope=claims.get('scope', []),
        tls_scheme=tls_validator.get_tls_scheme(tls_info),
        provider=provider.value
    )
    
    return claims


async def get_wells_apigee_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """FastAPI dependency for Apigee authentication."""
    return await get_wells_authenticated_user(request, credentials, AuthProvider.APIGEE)


async def get_wells_pingfed_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """FastAPI dependency for PingFederate authentication."""
    return await get_wells_authenticated_user(request, credentials, AuthProvider.PINGFED)


def require_wells_scope(required_scope: str):
    """
    FastAPI dependency factory to require specific scope for Wells Fargo auth.
    
    Args:
        required_scope: Required scope string
        
    Returns:
        FastAPI dependency function
    """
    async def scope_dependency(
        current_user: Dict[str, Any] = Depends(get_wells_authenticated_user)
    ) -> Dict[str, Any]:
        user_scopes = _extract_scopes(current_user)
        
        if required_scope not in user_scopes:
            logger.warning(
                "Insufficient scope for Wells Fargo user",
                required_scope=required_scope,
                user_scopes=user_scopes,
                sub=current_user.get('sub')
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "403",
                    "status": "auth_error",
                    "error_message": f"Insufficient scope. Required: {required_scope}"
                }
            )
        
        return current_user
    
    return scope_dependency


def _extract_scopes(claims: dict) -> list:
    """Extract scopes from JWT claims."""
    scope = claims.get('scope', [])
    if isinstance(scope, str):
        # Handle space-separated scopes
        return [s.strip() for s in scope.split() if s.strip()]
    elif isinstance(scope, list):
        return scope
    else:
        return []


async def get_wells_client_id(current_user: Dict[str, Any] = Depends(get_wells_authenticated_user)) -> str:
    """Get client ID from Wells Fargo authenticated user."""
    return current_user.get('client_id') or current_user.get('sub', 'unknown')


async def get_wells_user_id(current_user: Dict[str, Any] = Depends(get_wells_authenticated_user)) -> str:
    """Get user ID from Wells Fargo authenticated user."""
    return current_user.get('sub', 'unknown')


async def get_wells_user_scopes(current_user: Dict[str, Any] = Depends(get_wells_authenticated_user)) -> list:
    """Get user scopes from Wells Fargo authenticated user."""
    return _extract_scopes(current_user)


