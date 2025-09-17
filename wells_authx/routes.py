"""Wells Fargo AuthX specific routes for COP Guard."""

from typing import Dict, Any

from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import JSONResponse

from app.logging import get_logger
from .deps import get_wells_authenticated_user, get_wells_apigee_user, get_wells_pingfed_user
from .wells_authenticator import wells_authenticator

logger = get_logger(__name__)

router = APIRouter()


@router.post("/wells-auth/validate")
async def validate_wells_token(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_wells_authenticated_user)
) -> JSONResponse:
    """
    Validate JWT token using Wells Fargo AuthX.
    
    Args:
        request: FastAPI request object
        current_user: Wells Fargo authenticated user claims
        
    Returns:
        JSON response with claims or error
    """
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')
    
    logger.info(
        "Wells Fargo token validation requested",
        correlation_id=correlation_id,
        sub=current_user.get('sub'),
        client_id=current_user.get('client_id'),
        iss=current_user.get('iss'),
        aud=current_user.get('aud'),
        provider=getattr(request.state, 'auth_provider', 'unknown')
    )
    
    # Return success response with claims
    return JSONResponse(
        status_code=200,
        content={
            "code": "200",
            "status": "success",
            "provider": getattr(request.state, 'auth_provider', 'unknown'),
            "claims": current_user
        }
    )


@router.post("/wells-auth/validate/apigee")
async def validate_apigee_token(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_wells_apigee_user)
) -> JSONResponse:
    """
    Validate JWT token specifically using Apigee provider.
    
    Args:
        request: FastAPI request object
        current_user: Apigee authenticated user claims
        
    Returns:
        JSON response with claims or error
    """
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')
    
    logger.info(
        "Apigee token validation requested",
        correlation_id=correlation_id,
        sub=current_user.get('sub'),
        client_id=current_user.get('client_id'),
        iss=current_user.get('iss')
    )
    
    return JSONResponse(
        status_code=200,
        content={
            "code": "200",
            "status": "success",
            "provider": "apigee",
            "claims": current_user
        }
    )


@router.post("/wells-auth/validate/pingfed")
async def validate_pingfed_token(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_wells_pingfed_user)
) -> JSONResponse:
    """
    Validate JWT token specifically using PingFederate provider.
    
    Args:
        request: FastAPI request object
        current_user: PingFederate authenticated user claims
        
    Returns:
        JSON response with claims or error
    """
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')
    
    logger.info(
        "PingFederate token validation requested",
        correlation_id=correlation_id,
        sub=current_user.get('sub'),
        client_id=current_user.get('client_id'),
        iss=current_user.get('iss')
    )
    
    return JSONResponse(
        status_code=200,
        content={
            "code": "200",
            "status": "success",
            "provider": "pingfed",
            "claims": current_user
        }
    )


@router.get("/wells-auth/info")
async def get_wells_auth_info() -> JSONResponse:
    """
    Get Wells Fargo AuthX configuration information.
    
    Returns:
        JSON response with configuration details
    """
    try:
        provider_info = wells_authenticator.get_provider_info()
        
        return JSONResponse(
            status_code=200,
            content={
                "code": "200",
                "status": "success",
                "wells_authx_info": provider_info
            }
        )
    except Exception as e:
        logger.error("Failed to get Wells AuthX info", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "500",
                "status": "error",
                "error_message": "Failed to retrieve Wells AuthX information"
            }
        )


@router.get("/wells-auth/health")
async def wells_auth_health_check() -> JSONResponse:
    """
    Health check for Wells Fargo AuthX integration.
    
    Returns:
        JSON response with health status
    """
    try:
        provider_info = wells_authenticator.get_provider_info()
        
        # Check if authenticators are initialized
        health_status = "healthy" if provider_info.get("initialized", False) else "degraded"
        
        return JSONResponse(
            status_code=200,
            content={
                "code": "200",
                "status": "success",
                "health": health_status,
                "wells_authx_ready": provider_info.get("initialized", False),
                "environment": provider_info.get("environment", "unknown")
            }
        )
    except Exception as e:
        logger.error("Wells AuthX health check failed", error=str(e))
        return JSONResponse(
            status_code=503,
            content={
                "code": "503",
                "status": "error",
                "health": "unhealthy",
                "error_message": "Wells AuthX service unavailable"
            }
        )


