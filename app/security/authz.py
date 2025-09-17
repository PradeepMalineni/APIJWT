"""Authorization system with scope enforcement."""

from functools import wraps
from typing import List, Union

from fastapi import HTTPException, status

from app.logging import get_logger

logger = get_logger(__name__)


class AuthorizationError(Exception):
    """Custom exception for authorization errors."""
    pass


def require_scopes(required_scopes: Union[str, List[str]]):
    """
    Decorator to require specific scopes for route access.
    
    Args:
        required_scopes: Single scope string or list of scope strings
    """
    if isinstance(required_scopes, str):
        required_scopes = [required_scopes]
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get claims from request state (set by auth dependency)
            request = kwargs.get('request')
            if not request:
                # Try to find request in args
                for arg in args:
                    if hasattr(arg, 'state') and hasattr(arg.state, 'claims'):
                        request = arg
                        break
            
            if not request or not hasattr(request.state, 'claims'):
                logger.error("No claims found in request state")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "code": "401",
                        "status": "auth_error",
                        "error_message": "Authentication required"
                    }
                )
            
            claims = request.state.claims
            user_scopes = _extract_scopes(claims)
            
            # Check if user has any of the required scopes
            has_required_scope = any(scope in user_scopes for scope in required_scopes)
            
            if not has_required_scope:
                logger.warning(
                    "Insufficient scope",
                    required_scopes=required_scopes,
                    user_scopes=user_scopes,
                    sub=claims.get('sub'),
                    client_id=claims.get('client_id')
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "code": "403",
                        "status": "auth_error",
                        "error_message": f"Insufficient scope. Required: {', '.join(required_scopes)}"
                    }
                )
            
            logger.info(
                "Scope check passed",
                required_scopes=required_scopes,
                user_scopes=user_scopes,
                sub=claims.get('sub')
            )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def _extract_scopes(claims: dict) -> List[str]:
    """Extract scopes from JWT claims."""
    scope = claims.get('scope', [])
    if isinstance(scope, str):
        # Handle space-separated scopes
        return [s.strip() for s in scope.split() if s.strip()]
    elif isinstance(scope, list):
        return scope
    else:
        return []


def check_scope_access(claims: dict, required_scopes: Union[str, List[str]]) -> bool:
    """
    Check if claims contain required scopes.
    
    Args:
        claims: JWT claims dictionary
        required_scopes: Single scope string or list of scope strings
        
    Returns:
        True if user has any of the required scopes
    """
    if isinstance(required_scopes, str):
        required_scopes = [required_scopes]
    
    user_scopes = _extract_scopes(claims)
    return any(scope in user_scopes for scope in required_scopes)


def get_user_scopes(claims: dict) -> List[str]:
    """Get user scopes from claims."""
    return _extract_scopes(claims)


def get_client_id(claims: dict) -> str:
    """Get client ID from claims."""
    return claims.get('client_id') or claims.get('sub', 'unknown')


def get_user_id(claims: dict) -> str:
    """Get user ID from claims."""
    return claims.get('sub', 'unknown')


def log_authorization_decision(
    decision: str,
    claims: dict,
    required_scopes: List[str] = None,
    reason: str = None
) -> None:
    """Log authorization decision for audit trail."""
    log_data = {
        "decision": decision,
        "sub": claims.get('sub'),
        "client_id": get_client_id(claims),
        "iss": claims.get('iss'),
        "aud": claims.get('aud'),
        "user_scopes": get_user_scopes(claims)
    }
    
    if required_scopes:
        log_data["required_scopes"] = required_scopes
    
    if reason:
        log_data["reason"] = reason
    
    if decision == "allow":
        logger.info("Authorization decision: ALLOW", **log_data)
    else:
        logger.warning("Authorization decision: DENY", **log_data)
