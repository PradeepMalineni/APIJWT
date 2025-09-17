"""Main FastAPI application with all middleware and routes."""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.logging import setup_logging, get_logger
from app.middleware.correlation import CorrelationIDMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.security.jwks_cache import jwks_cache
from app.api import routes_public, routes_auth, routes_onboarding

# Setup logging
setup_logging(settings.log_level)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting COP Guard API protection layer")
    
    # Initialize JWKS cache
    try:
        await jwks_cache.initialize()
        logger.info("JWKS cache initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize JWKS cache", error=str(e))
        # Don't fail startup - service can still run with limited functionality
    
    yield
    
    # Shutdown
    logger.info("Shutting down COP Guard API protection layer")
    
    # Stop JWKS background refresh
    try:
        await jwks_cache.stop_background_refresh()
        logger.info("JWKS background refresh stopped")
    except Exception as e:
        logger.error("Error stopping JWKS background refresh", error=str(e))


# Create FastAPI application
app = FastAPI(
    title="COP Guard API Protection Layer",
    description="Production-ready API protection layer for COP APIs called by IDP",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.log_level == "DEBUG" else None,
    redoc_url="/redoc" if settings.log_level == "DEBUG" else None,
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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure appropriately for production
)

# Add correlation ID middleware
app.add_middleware(CorrelationIDMiddleware)

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')
    
    logger.error(
        "Unhandled exception",
        correlation_id=correlation_id,
        error=str(exc),
        method=request.method,
        url=str(request.url)
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "code": "500",
            "status": "internal_error",
            "error_message": "Internal server error"
        }
    )

# Include routers
app.include_router(routes_public.router, tags=["public"])
app.include_router(routes_auth.router, prefix="/api/v1", tags=["authentication"])
app.include_router(routes_onboarding.router, prefix="/api/v1", tags=["onboarding"])

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "COP Guard API Protection Layer",
        "version": "1.0.0",
        "status": "running"
    }

# Health check endpoint (alternative to /healthz)
@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "cop-guard",
        "version": "1.0.0"
    }

# Metrics endpoint (if enabled)
if settings.enable_metrics:
    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint."""
        # Basic metrics - in production you'd use prometheus_client
        return {
            "service": "cop-guard",
            "version": "1.0.0",
            "status": "healthy"
        }

if __name__ == "__main__":
    import uvicorn
    
    logger.info(
        "Starting COP Guard API protection layer",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level
    )
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        reload=settings.log_level == "DEBUG"
    )
