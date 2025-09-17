"""Wells Fargo AuthX FastAPI application - Standalone version."""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import wells_auth_config
from wells_authenticator import wells_authenticator
from routes import router as wells_authx_router

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Wells Fargo AuthX service")
    
    # Initialize Wells authenticator
    try:
        await wells_authenticator._initialize_authenticator()
        logger.info("Wells Fargo AuthX authenticator initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Wells AuthX authenticator: {e}")
        # Don't fail startup - service can still run with limited functionality
    
    yield
    
    # Shutdown
    logger.info("Shutting down Wells Fargo AuthX service")


# Create FastAPI application
app = FastAPI(
    title="Wells Fargo AuthX Service",
    description="Wells Fargo AuthX JWT token validation service - Apigee Only",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response

# Add correlation ID middleware (simplified)
@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    """Add correlation ID to requests."""
    import uuid
    correlation_id = str(uuid.uuid4())
    request.state.correlation_id = correlation_id
    
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')
    
    logger.error(
        f"Unhandled exception - {correlation_id}: {exc}",
        extra={
            "correlation_id": correlation_id,
            "error": str(exc),
            "method": request.method,
            "url": str(request.url)
        }
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "code": "500",
            "status": "internal_error",
            "error_message": "Internal server error"
        }
    )

# Include Wells AuthX router
app.include_router(wells_authx_router, prefix="/api/v1", tags=["wells-authx"])

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Wells Fargo AuthX Service",
        "version": "1.0.0",
        "status": "running",
        "provider": "apigee"
    }

# Health check endpoint
@app.get("/health")
async def health():
    """Health check endpoint."""
    try:
        provider_info = wells_authenticator.get_provider_info()
        health_status = "healthy" if provider_info.get("initialized", False) else "degraded"
        
        return {
            "status": health_status,
            "service": "wells-authx",
            "version": "1.0.0",
            "provider": "apigee",
            "environment": wells_auth_config.environment,
            "initialized": provider_info.get("initialized", False)
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "wells-authx",
                "version": "1.0.0",
                "error": str(e)
            }
        )

# Configuration endpoint
@app.get("/config")
async def get_config():
    """Get current configuration (non-sensitive info only)."""
    return {
        "environment": wells_auth_config.environment,
        "auto_refresh": wells_auth_config.auto_refresh,
        "validate_claims": wells_auth_config.validate_claims,
        "validate_certificate": wells_auth_config.validate_certificate,
        "provider": "apigee"
    }


if __name__ == "__main__":
    import uvicorn
    
    # Get configuration
    host = "0.0.0.0"
    port = 8000
    log_level = "info"
    
    # Override with environment variables if available
    import os
    host = os.getenv("HOST", host)
    port = int(os.getenv("PORT", port))
    log_level = os.getenv("LOG_LEVEL", log_level).lower()
    
    logger.info(f"Starting Wells Fargo AuthX service on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        log_level=log_level,
        reload=log_level == "debug"
    )