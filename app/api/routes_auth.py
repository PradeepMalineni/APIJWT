"""Authentication routes for JWT validation."""

from typing import Dict, Any

from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import JSONResponse

from app.logging import get_logger
from app.security.deps import get_current_user

logger = get_logger(__name__)

router = APIRouter()


@router.post("/auth/validate")
async def validate_token(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> JSONResponse:
    """
    Validate JWT token and return claims.
    
    Args:
        request: FastAPI request object
        current_user: JWT claims from authentication dependency
        
    Returns:
        JSON response with claims or error
    """
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')
    
    logger.info(
        "Token validation requested",
        correlation_id=correlation_id,
        sub=current_user.get('sub'),
        client_id=current_user.get('client_id'),
        iss=current_user.get('iss'),
        aud=current_user.get('aud')
    )
    
    # Return success response with claims
    return JSONResponse(
        status_code=200,
        content={
            "code": "200",
            "status": "success",
            "claims": current_user
        }
    )
