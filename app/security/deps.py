"""FastAPI dependencies for authentication and authorization."""

from typing import Optional, Dict, Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.logging import get_logger
from app.security.jwt_validator import jwt_validator
from app.security.mtls import tls_validator

logger = get_logger(__name__)

# HTTP Bearer token security scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """
    FastAPI dependency to extract and validate JWT token.
    
    Args:
        request: FastAPI request object
        credentials: HTTP Bearer credentials
        
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
    
    # Validate JWT
    claims, error = await jwt_validator.validate_jwt(token)
    
    if error:
        logger.warning("JWT validation failed", error=error)
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
    
    # Log successful authentication
    logger.info(
        "User authenticated successfully",
        sub=claims.get('sub'),
        client_id=claims.get('client_id'),
        iss=claims.get('iss'),
        aud=claims.get('aud'),
        scope=claims.get('scope', []),
        tls_scheme=tls_validator.get_tls_scheme(tls_info)
    )
    
    return claims


async def get_optional_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict[str, Any]]:
    """
    FastAPI dependency to optionally extract and validate JWT token.
    
    Args:
        request: FastAPI request object
        credentials: HTTP Bearer credentials
        
    Returns:
        JWT claims dictionary or None if no token provided
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(request, credentials)
    except HTTPException:
        # Re-raise authentication errors
        raise
    except Exception as e:
        logger.error("Unexpected error in optional authentication", error=str(e))
        return None


def require_scope(required_scope: str):
    """
    FastAPI dependency factory to require specific scope.
    
    Args:
        required_scope: Required scope string
        
    Returns:
        FastAPI dependency function
    """
    async def scope_dependency(
        current_user: Dict[str, Any] = Depends(get_current_user)
    ) -> Dict[str, Any]:
        user_scopes = jwt_validator.extract_scope(current_user)
        
        if required_scope not in user_scopes:
            logger.warning(
                "Insufficient scope",
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


def require_any_scope(required_scopes: list):
    """
    FastAPI dependency factory to require any of the specified scopes.
    
    Args:
        required_scopes: List of required scope strings
        
    Returns:
        FastAPI dependency function
    """
    async def scope_dependency(
        current_user: Dict[str, Any] = Depends(get_current_user)
    ) -> Dict[str, Any]:
        user_scopes = jwt_validator.extract_scope(current_user)
        
        has_required_scope = any(scope in user_scopes for scope in required_scopes)
        
        if not has_required_scope:
            logger.warning(
                "Insufficient scope",
                required_scopes=required_scopes,
                user_scopes=user_scopes,
                sub=current_user.get('sub')
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "403",
                    "status": "auth_error",
                    "error_message": f"Insufficient scope. Required: {', '.join(required_scopes)}"
                }
            )
        
        return current_user
    
    return scope_dependency


async def get_client_id(current_user: Dict[str, Any] = Depends(get_current_user)) -> str:
    """
    FastAPI dependency to extract client ID from JWT claims.
    
    Args:
        current_user: JWT claims from get_current_user dependency
        
    Returns:
        Client ID string
    """
    return current_user.get('client_id') or current_user.get('sub', 'unknown')


async def get_user_id(current_user: Dict[str, Any] = Depends(get_current_user)) -> str:
    """
    FastAPI dependency to extract user ID from JWT claims.
    
    Args:
        current_user: JWT claims from get_current_user dependency
        
    Returns:
        User ID string
    """
    return current_user.get('sub', 'unknown')


async def get_user_scopes(current_user: Dict[str, Any] = Depends(get_current_user)) -> list:
    """
    FastAPI dependency to extract user scopes from JWT claims.
    
    Args:
        current_user: JWT claims from get_current_user dependency
        
    Returns:
        List of user scopes
    """
    return jwt_validator.extract_scope(current_user)
