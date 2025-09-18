"""Wells Fargo AuthX Flask application - Standalone version."""

import asyncio
import logging
import uuid
import os
from functools import wraps
from typing import Dict, Any, Optional, Tuple

from flask import Flask, request, jsonify, g
from flask_cors import CORS

# Import with error handling
try:
    from config import WellsAuthConfig
    from security import WellsAuthenticator, container, get_wells_authenticated_user
    from routes import register_routes
except ImportError as e:
    logging.error(f"Failed to import required modules: {e}")
    raise RuntimeError(f"Missing required dependencies: {e}")

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize configuration and dependencies
try:
    wells_auth_config = WellsAuthConfig()
    wells_authenticator = WellsAuthenticator()
    
    # Configure dependency injection container
    container.set_config(wells_auth_config)
    container.set_authenticator(wells_authenticator)
    
    logger.info("Wells Fargo AuthX configuration initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Wells Fargo AuthX configuration: {e}")
    raise RuntimeError(f"Configuration initialization failed: {e}")

# Create Flask application
app = Flask(__name__)
CORS(app)

# Configuration
app.config['JSON_SORT_KEYS'] = False

# Register Routes
register_routes(app)

# Add Wells Fargo AuthX specific routes
from flask import Blueprint

# Create Wells Fargo AuthX Blueprint
wells_authx_bp = Blueprint('wells_authx', __name__, url_prefix='/api/v1')

@wells_authx_bp.route("/wells-auth/validate", methods=["POST"])
@get_wells_authenticated_user
def validate_wells_token():
    """Validate JWT token using Wells Fargo AuthX Apigee."""
    current_user = g.current_user
    correlation_id = getattr(g, 'correlation_id', 'unknown')
    
    logger.info(
        "Wells Fargo Apigee token validation requested",
        extra={
            "correlation_id": correlation_id,
            "sub": current_user.get('sub'),
            "client_id": current_user.get('client_id'),
            "iss": current_user.get('iss'),
            "aud": current_user.get('aud'),
            "provider": getattr(g, 'auth_provider', 'apigee')
        }
    )
    
    return jsonify({
        "code": "200",
        "status": "success",
        "provider": "apigee",
        "claims": current_user,
        "correlation_id": correlation_id
    })

@wells_authx_bp.route("/wells-auth/info", methods=["GET"])
def get_wells_auth_info():
    """Get Wells Fargo AuthX Apigee configuration information."""
    try:
        authenticator = container.get_authenticator()
        provider_info = authenticator.get_provider_info()
        
        return jsonify({
            "code": "200",
            "status": "success",
            "wells_authx_info": provider_info
        })
    except Exception as e:
        logger.error("Failed to get Wells AuthX info", extra={"error": str(e)})
        return jsonify({
            "code": "500",
            "status": "error",
            "error_message": "Failed to retrieve Wells AuthX information"
        }), 500

@wells_authx_bp.route("/wells-auth/health", methods=["GET"])
def wells_auth_health_check():
    """Health check for Wells Fargo AuthX Apigee integration."""
    try:
        authenticator = container.get_authenticator()
        provider_info = authenticator.get_provider_info()
        
        health_status = "healthy" if provider_info.get("initialized", False) else "degraded"
        
        return jsonify({
            "code": "200",
            "status": "success",
            "health": health_status,
            "wells_authx_ready": provider_info.get("initialized", False),
            "environment": provider_info.get("environment", "unknown"),
            "provider": "apigee"
        })
    except Exception as e:
        logger.error("Wells AuthX health check failed", extra={"error": str(e)})
        return jsonify({
            "code": "503",
            "status": "error",
            "health": "unhealthy",
            "error_message": "Wells AuthX Apigee service unavailable"
        }), 503

# Register Wells Fargo AuthX Blueprint
app.register_blueprint(wells_authx_bp)


def add_security_headers(response):
    """Add modern security headers to all responses."""
    # Prevent MIME type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"
    
    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"
    
    # Control referrer information
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Enforce HTTPS (only if not behind a proxy that handles this)
    if not os.getenv("BEHIND_PROXY", "false").lower() == "true":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    
    # Content Security Policy (basic)
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'"
    
    # Permissions Policy (formerly Feature Policy)
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    
    # Remove server information
    response.headers.pop("Server", None)
    
    return response


def add_correlation_id():
    """Add correlation ID to requests."""
    correlation_id = str(uuid.uuid4())
    g.correlation_id = correlation_id
    return correlation_id


@app.before_request
def before_request():
    """Execute before each request."""
    add_correlation_id()


@app.after_request
def after_request(response):
    """Execute after each request."""
    # Add correlation ID to response headers
    if hasattr(g, 'correlation_id'):
        response.headers["X-Correlation-ID"] = g.correlation_id
    
    # Add security headers
    response = add_security_headers(response)
    return response


# Error handlers
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        "code": "404",
        "status": "error",
        "error_message": "Endpoint not found"
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    correlation_id = getattr(g, 'correlation_id', 'unknown')
    logger.error(f"Internal server error - {correlation_id}: {error}")
    
    return jsonify({
        "code": "500",
        "status": "internal_error",
        "error_message": "Internal server error"
    }), 500


# Routes
@app.route("/", methods=["GET"])
def root():
    """Root endpoint."""
    return jsonify({
        "service": "Wells Fargo AuthX Service",
        "version": "1.0.0",
        "status": "running",
        "provider": "apigee"
    })


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    try:
        authenticator = container.get_authenticator()
        config = container.get_config()
        provider_info = authenticator.get_provider_info()
        health_status = "healthy" if provider_info.get("initialized", False) else "degraded"
        
        return jsonify({
            "status": health_status,
            "service": "wells-authx",
            "version": "1.0.0",
            "provider": "apigee",
            "environment": config.environment,
            "initialized": provider_info.get("initialized", False)
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "service": "wells-authx",
            "version": "1.0.0",
            "error": str(e)
        }), 503


@app.route("/config", methods=["GET"])
def get_config():
    """Get current configuration (non-sensitive info only)."""
    try:
        config = container.get_config()
        return jsonify({
            "environment": config.environment,
            "auto_refresh": config.auto_refresh,
            "validate_claims": config.validate_claims,
            "validate_certificate": config.validate_certificate,
            "provider": "apigee"
        })
    except Exception as e:
        logger.error(f"Failed to get configuration: {e}")
        return jsonify({
            "code": "500",
            "status": "error",
            "error_message": "Failed to retrieve configuration"
        }), 500


if __name__ == "__main__":
    import os
    
    # Get configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    debug = os.getenv("LOG_LEVEL", "info").lower() == "debug"
    
    logger.info(f"Starting Wells Fargo AuthX Flask service on {host}:{port}")
    
    app.run(
        host=host,
        port=port,
        debug=debug
    )