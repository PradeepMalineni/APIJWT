"""Public routes that don't require authentication."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from app.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/healthz")
async def health_check(request: Request):
    """
    Health check endpoint.
    
    Returns:
        JSON response with health status
    """
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')
    
    logger.info(
        "Health check requested",
        correlation_id=correlation_id,
        method=request.method,
        url=str(request.url)
    )
    
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": "cop-guard",
            "version": "1.0.0"
        }
    )
