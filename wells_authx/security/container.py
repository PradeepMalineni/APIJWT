"""Dependency injection container for Wells Fargo AuthX Flask application."""

import asyncio
import logging
from typing import Optional, Dict, Any, Tuple, Protocol
from functools import wraps

from flask import request, jsonify, g

logger = logging.getLogger(__name__)


class WellsAuthenticatorProtocol(Protocol):
    """Protocol for Wells Fargo authenticator."""
    
    async def authenticate_token(
        self, 
        token: str, 
        client_id: Optional[str] = None
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Authenticate JWT token."""
        ...
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider information."""
        ...


class DependencyContainer:
    """Dependency injection container."""
    
    def __init__(self):
        self._authenticator: Optional[WellsAuthenticatorProtocol] = None
        self._config = None
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None
    
    def set_authenticator(self, authenticator: WellsAuthenticatorProtocol):
        """Set the authenticator instance."""
        self._authenticator = authenticator
    
    def get_authenticator(self) -> WellsAuthenticatorProtocol:
        """Get the authenticator instance."""
        if self._authenticator is None:
            raise RuntimeError("Authenticator not configured. Call set_authenticator() first.")
        return self._authenticator
    
    def set_config(self, config):
        """Set the configuration instance."""
        self._config = config
    
    def get_config(self):
        """Get the configuration instance."""
        if self._config is None:
            raise RuntimeError("Configuration not set. Call set_config() first.")
        return self._config
    
    def get_event_loop(self) -> asyncio.AbstractEventLoop:
        """Get or create event loop for async operations."""
        if self._event_loop is None or self._event_loop.is_closed():
            try:
                # Try to get the current event loop
                self._event_loop = asyncio.get_event_loop()
            except RuntimeError:
                # Create a new event loop if none exists
                self._event_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._event_loop)
        return self._event_loop


# Global container instance
container = DependencyContainer()


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
        authenticator = container.get_authenticator()
        
        # Authenticate using Wells Fargo AuthX Apigee
        claims, error = await authenticator.authenticate_token(token)
        
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
        
        # Authenticate token using proper async handling
        try:
            # Get the event loop from container
            loop = container.get_event_loop()
            
            # Run async authentication in the existing event loop
            if loop.is_running():
                # If we're already in an async context, create a task
                task = asyncio.create_task(authenticate_wells_token(token))
                # This is a simplified approach - in production you might want to use
                # a different pattern like asyncio.run_coroutine_threadsafe
                claims, error = None, "Async context not properly handled"
                logger.warning("Running in async context - consider using async route handlers")
            else:
                # Run in the event loop
                claims, error = loop.run_until_complete(authenticate_wells_token(token))
            
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
