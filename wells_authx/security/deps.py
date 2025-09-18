"""Flask decorators for Wells Fargo AuthX integration - Apigee Only."""

import asyncio
import logging
from functools import wraps
from typing import Optional, Dict, Any, Tuple

from flask import request, jsonify, g

from wells_authenticator import wells_authenticator

logger = logging.getLogger(__name__)


def get_authorization_header() -> Optional[str]:
    """Extract Authorization header from request."""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None
    
    if not auth_header.startswith('Bearer '):
        return None
    
    return auth_header[7:]  # Remove 'Bearer ' prefix


async def authenticate_wells_token(token: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Authenticate JWT token using Wells Fargo AuthX Apigee.
    
    Args:
        token: JWT token to authenticate
        
    Returns:
        Tuple of (claims_dict, error_message)
    """
    try:
        await wells_authenticator._initialize_authenticator()
        
        # Authenticate using Wells Fargo AuthX Apigee
        claims, error = await wells_authenticator.authenticate_token(token)
        
        if error:
            logger.warning("Wells Fargo Apigee authentication failed", extra={"error": error})
            return None, error
        
        # Log successful authentication
        logger.info(
            "User authenticated successfully via Wells Fargo AuthX Apigee",
            extra={
                "sub": claims.get('sub'),
                "client_id": claims.get('client_id'),
                "iss": claims.get('iss'),
                "aud": claims.get('aud'),
                "scope": claims.get('scope', [])
            }
        )
        
        return claims, None
        
    except Exception as e:
        error_msg = f"Authentication error: {str(e)}"
        logger.error("Token authentication error via Apigee", extra={"error": str(e)})
        return None, error_msg


def get_wells_authenticated_user(f):
    """
    Flask decorator to authenticate using Wells Fargo AuthX Apigee.
    This is the main authentication decorator for all Wells Fargo AuthX endpoints.
    
    Usage:
        @app.route("/protected")
        @get_wells_authenticated_user
        def protected_route():
            # Access authenticated user via g.current_user
            user = g.current_user
            return {"user": user}
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Extract JWT token
        token = get_authorization_header()
        if not token:
            logger.warning("No authorization header provided")
            return jsonify({
                "code": "401",
                "status": "auth_error",
                "error_message": "Authorization header required"
            }), 401
        
        # Authenticate token
        try:
            # Run async authentication in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            claims, error = loop.run_until_complete(authenticate_wells_token(token))
            loop.close()
            
            if error:
                return jsonify({
                    "code": "401",
                    "status": "auth_error",
                    "error_message": error
                }), 401
            
            # Store claims in Flask's g object for use in route
            g.current_user = claims
            g.auth_provider = "apigee"
            
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return jsonify({
                "code": "401",
                "status": "auth_error",
                "error_message": f"Authentication error: {str(e)}"
            }), 401
    
    return decorated_function


# Alias for backward compatibility (deprecated - use get_wells_authenticated_user instead)
def get_wells_apigee_user(f):
    """
    Flask decorator for Apigee authentication (alias for get_wells_authenticated_user).
    
    DEPRECATED: Use get_wells_authenticated_user instead.
    This alias is maintained for backward compatibility only.
    
    Usage:
        @app.route("/apigee-protected")
        @get_wells_apigee_user  # Same as @get_wells_authenticated_user
        def apigee_route():
            user = g.current_user
            return {"user": user}
    """
    return get_wells_authenticated_user(f)


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


def require_wells_scope(required_scope: str):
    """
    Flask decorator factory to require specific scope for Wells Fargo auth.
    
    Args:
        required_scope: Required scope string
        
    Returns:
        Flask decorator function
        
    Usage:
        @app.route("/admin")
        @get_wells_authenticated_user
        @require_wells_scope("admin")
        def admin_route():
            return {"message": "Admin access granted"}
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # First check authentication
            if not hasattr(g, 'current_user'):
                return jsonify({
                    "code": "401",
                    "status": "auth_error",
                    "error_message": "Authentication required"
                }), 401
            
            # Extract scopes from claims
            user_scopes = _extract_scopes(g.current_user)
            
            if required_scope not in user_scopes:
                logger.warning(
                    "Insufficient scope for Wells Fargo Apigee user",
                    extra={
                        "required_scope": required_scope,
                        "user_scopes": user_scopes,
                        "sub": g.current_user.get('sub')
                    }
                )
                return jsonify({
                    "code": "403",
                    "status": "auth_error",
                    "error_message": f"Insufficient scope. Required: {required_scope}"
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def get_wells_client_id() -> str:
    """Get client ID from Wells Fargo Apigee authenticated user."""
    if not hasattr(g, 'current_user'):
        return 'unknown'
    return g.current_user.get('client_id') or g.current_user.get('sub', 'unknown')


def get_wells_user_id() -> str:
    """Get user ID from Wells Fargo Apigee authenticated user."""
    if not hasattr(g, 'current_user'):
        return 'unknown'
    return g.current_user.get('sub', 'unknown')


def get_wells_user_scopes() -> list:
    """Get user scopes from Wells Fargo Apigee authenticated user."""
    if not hasattr(g, 'current_user'):
        return []
    return _extract_scopes(g.current_user)