"""Rate limiting middleware using slowapi."""

from typing import Callable, Optional

from fastapi import Request, Response, HTTPException, status
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.logging import get_logger

logger = get_logger(__name__)


def get_client_identifier(request: Request) -> str:
    """
    Get client identifier for rate limiting.
    
    Priority:
    1. client_id from JWT claims (if available)
    2. Remote IP address
    """
    # Try to get client_id from request state (set by auth middleware)
    if hasattr(request.state, 'claims'):
        client_id = request.state.claims.get('client_id')
        if client_id:
            return f"client:{client_id}"
    
    # Fall back to IP address
    return f"ip:{get_remote_address(request)}"


# Initialize limiter
limiter = Limiter(
    key_func=get_client_identifier,
    default_limits=[f"{settings.rate_limit_default_per_min}/minute"]
)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware wrapper."""
    
    def __init__(self, app):
        super().__init__(app)
        # Set up rate limit exceeded handler
        self.app.state.limiter = limiter
        self.app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting."""
        try:
            # Check rate limit
            limiter._check_request_limit(request)
            
            # Process request
            response = await call_next(request)
            
            # Log rate limit status
            client_id = get_client_identifier(request)
            logger.debug(
                "Rate limit check passed",
                client_id=client_id,
                method=request.method,
                url=str(request.url)
            )
            
            return response
            
        except RateLimitExceeded as e:
            # Log rate limit exceeded
            client_id = get_client_identifier(request)
            logger.warning(
                "Rate limit exceeded",
                client_id=client_id,
                method=request.method,
                url=str(request.url),
                limit=str(e.detail)
            )
            
            # Return rate limit error
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "code": "429",
                    "status": "rate_limit_exceeded",
                    "error_message": "Rate limit exceeded. Please try again later."
                }
            )


def rate_limit(limit: str):
    """
    Decorator for per-route rate limiting.
    
    Args:
        limit: Rate limit string (e.g., "10/minute", "100/hour")
    """
    return limiter.limit(limit)
