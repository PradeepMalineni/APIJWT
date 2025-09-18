# COP Guard - How To Guide

This guide provides step-by-step instructions for setting up, configuring, and using the COP Guard API protection layer with Wells Fargo AuthX integration.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Running the Service](#running-the-service)
5. [Testing](#testing)
6. [Wells Fargo AuthX Integration](#wells-fargo-authx-integration)
7. [API Usage Examples](#api-usage-examples)
8. [Development](#development)
9. [Troubleshooting](#troubleshooting)
10. [Production Deployment](#production-deployment)

## Quick Start

### Prerequisites

- Python 3.11+
- Docker (optional)
- Wells Fargo AuthX access (for Wells Fargo integration)

### 1. Clone and Setup

```bash
# Navigate to project directory
cd /Users/pradeepm/ProjX/APIM_JWT/cop-guard

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev,test]"
```

### 2. Basic Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
nano .env
```

### 3. Run the Service

```bash
# Start the service
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

### 4. Test Health Check

```bash
curl http://localhost:8080/healthz
```

## Installation

### Option 1: Local Development

```bash
# 1. Create virtual environment
python -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -e ".[dev,test]"

# 3. Install Wells Fargo AuthX (if needed)
pip install wellsfargo_ebssh_python_auth>=1.0.71
```

### Option 2: Docker

```bash
# 1. Build Docker image
docker build -t cop-guard .

# 2. Run container
docker run -p 8080:8080 \
  -e COP_AUDIENCE=TSIAM \
  -e ALLOWED_ISSUERS=https://idp.example/issuer \
  -e JWKS_URL_PRIMARY=https://jwks.example/apigee \
  cop-guard
```

### Option 3: Using Makefile

```bash
# Setup development environment
make dev-setup

# Run the service
make run

# Run tests
make test

# Run linting
make lint
```

## Configuration

### Environment Variables

Create a `.env` file with the following configuration:

```bash
# Server Configuration
PORT=8080
HOST=0.0.0.0

# JWT/Auth Configuration
COP_AUDIENCE=TSIAM
ALLOWED_ISSUERS=https://idp.example/issuer,https://ping.example/issuer
JWKS_URL_PRIMARY=https://jwks.example/apigee
JWKS_URL_SECONDARY=https://jwks.example/ping
JWKS_CACHE_TTL_SEC=900
JWKS_BACKGROUND_REFRESH_SEC=600
MAX_CLOCK_SKEW_SEC=120

# TLS Configuration
TLS_ENABLED=true

# Rate Limiting
RATE_LIMIT_DEFAULT_PER_MIN=100

# Logging
LOG_LEVEL=INFO

# Metrics
ENABLE_METRICS=false

# Wells Fargo AuthX Configuration (Optional)
WELLS_AUTH_ENVIRONMENT=dev
WELLS_AUTH_APIGEE_JWKS_URL=https://jwks-service-dev.cfapps.wellsfargo.net/publickey/getKeys
WELLS_AUTH_PINGFED_JWKS_URL=https://cspf-sit.wellsfargo.net/pf/JWKS
WELLS_AUTH_APIGEE_CLIENT_ID=EBSSH
WELLS_AUTH_PINGFED_CLIENT_ID=EBSSH
WELLS_AUTH_AUTO_REFRESH=true
```

### Configuration Options

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `PORT` | Server port | `8080` | No |
| `COP_AUDIENCE` | Expected JWT audience | `TSIAM` | Yes |
| `ALLOWED_ISSUERS` | Comma-separated allowed issuers | - | Yes |
| `JWKS_URL_PRIMARY` | Primary JWKS endpoint | - | Yes |
| `JWKS_URL_SECONDARY` | Secondary JWKS endpoint | - | No |
| `TLS_ENABLED` | Enable HTTPS enforcement | `true` | No |
| `WELLS_AUTH_ENVIRONMENT` | Wells Fargo environment (dev/sit/prod) | `dev` | No |

## Running the Service

### Development Mode

```bash
# With auto-reload
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

# With debug logging
LOG_LEVEL=DEBUG uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

### Production Mode

```bash
# Single worker
uvicorn app.main:app --host 0.0.0.0 --port 8080

# Multiple workers
uvicorn app.main:app --host 0.0.0.0 --port 8080 --workers 4
```

### Using Makefile

```bash
# Development
make run

# Production
make run-prod
```

## Testing

### Generate Test Tokens

```bash
# Generate sample JWT tokens for testing
python scripts/gen_test_tokens.py

# This creates:
# - scripts/private_key.pem
# - scripts/public_key.pem
# - scripts/token_valid.txt
# - scripts/token_expired.txt
# - scripts/token_wrong_aud.txt
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_health.py

# Run Wells Fargo AuthX tests
pytest tests/test_wells_authx.py
```

### Manual Testing

```bash
# Health check
curl http://localhost:8080/healthz

# Standard JWT validation
curl -X POST http://localhost:8080/api/v1/auth/validate \
  -H "Authorization: Bearer $(cat scripts/token_valid.txt)"

# Wells Fargo AuthX validation
curl -X POST http://localhost:8080/api/v1/wells-auth/validate \
  -H "Authorization: Bearer <your-wells-jwt-token>"
```

## Wells Fargo AuthX Integration

### Setup Wells Fargo AuthX

1. **Install Wells Fargo Package:**
   ```bash
   pip install wellsfargo_ebssh_python_auth>=1.0.71
   ```

2. **Configure Environment:**
   ```bash
   export WELLS_AUTH_ENVIRONMENT=dev
   export WELLS_AUTH_APIGEE_CLIENT_ID=EBSSH
   export WELLS_AUTH_PINGFED_CLIENT_ID=EBSSH
   ```

3. **Test Wells Fargo Integration:**
   ```bash
   # Check Wells Fargo AuthX info
   curl http://localhost:8080/api/v1/wells-auth/info
   
   # Health check
   curl http://localhost:8080/api/v1/wells-auth/health
   ```

### Wells Fargo Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/wells-auth/validate` | POST | Auto-detect provider and validate |
| `/api/v1/wells-auth/validate/apigee` | POST | Apigee-specific validation |
| `/api/v1/wells-auth/validate/pingfed` | POST | PingFederate-specific validation |
| `/api/v1/wells-auth/info` | GET | Configuration information |
| `/api/v1/wells-auth/health` | GET | Health check |

### Wells Fargo Configuration

```bash
# Environment-specific JWKS URLs (auto-detected)
WELLS_AUTH_ENVIRONMENT=dev    # dev, sit, prod
WELLS_AUTH_ENVIRONMENT=sit
WELLS_AUTH_ENVIRONMENT=prod

# Custom JWKS URLs (optional)
WELLS_AUTH_APIGEE_JWKS_URL=https://your-custom-apigee-jwks-url
WELLS_AUTH_PINGFED_JWKS_URL=https://your-custom-pingfed-jwks-url

# Client IDs
WELLS_AUTH_APIGEE_CLIENT_ID=EBSSH
WELLS_AUTH_PINGFED_CLIENT_ID=EBSSH

# Auto-refresh settings
WELLS_AUTH_AUTO_REFRESH=true
```

## API Usage Examples

### Health Checks

```bash
# Basic health check
curl http://localhost:8080/healthz

# Alternative health check
curl http://localhost:8080/health

# Wells Fargo AuthX health
curl http://localhost:8080/api/v1/wells-auth/health
```

### JWT Validation

#### Standard JWT Validation

```bash
# Validate JWT token
curl -X POST http://localhost:8080/api/v1/auth/validate \
  -H "Authorization: Bearer <your-jwt-token>"

# Expected response:
{
  "code": "200",
  "status": "success",
  "claims": {
    "aud": "TSIAM",
    "scope": ["TSIAM-Read", "TSIAM-Write"],
    "sub": "EBSSH",
    "jti": "uuid-here",
    "nbf": 1746523720,
    "iat": 1746523720,
    "exp": 1746524020
  }
}
```

#### Wells Fargo AuthX Validation

```bash
# Auto-detect provider
curl -X POST http://localhost:8080/api/v1/wells-auth/validate \
  -H "Authorization: Bearer <your-wells-jwt-token>"

# Apigee-specific
curl -X POST http://localhost:8080/api/v1/wells-auth/validate/apigee \
  -H "Authorization: Bearer <your-apigee-jwt-token>"

# PingFederate-specific
curl -X POST http://localhost:8080/api/v1/wells-auth/validate/pingfed \
  -H "Authorization: Bearer <your-pingfed-jwt-token>"

# Expected response:
{
  "code": "200",
  "status": "success",
  "provider": "apigee",
  "claims": {
    "aud": "TSIAM",
    "scope": ["TSIAM-Read", "TSIAM-Write"],
    "sub": "EBSSH",
    "jti": "uuid-here",
    "nbf": 1746523720,
    "iat": 1746523720,
    "exp": 1746524020,
    "iss": "https://apigee.wellsfargo.net/issuer"
  }
}
```

### Protected Endpoints

```bash
# List applications (requires TSIAM-Read scope)
curl -X GET http://localhost:8080/api/v1/onboarding/apps \
  -H "Authorization: Bearer <your-jwt-token>"

# Create application (requires TSIAM-Write scope)
curl -X POST http://localhost:8080/api/v1/onboarding/apps \
  -H "Authorization: Bearer <your-jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "My Application", "description": "A test application"}'
```

### Error Responses

```bash
# Expired token
{
  "code": "401",
  "status": "auth_error",
  "error_message": "Token validation failed: Token has expired."
}

# Wrong audience
{
  "code": "401",
  "status": "auth_error",
  "error_message": "Token validation failed: Invalid audience."
}

# Rate limit exceeded
{
  "code": "429",
  "status": "rate_limit_exceeded",
  "error_message": "Rate limit exceeded. Please try again later."
}
```

## Development

### Code Quality

```bash
# Run linting
ruff check app/ tests/

# Format code
ruff format app/ tests/

# Type checking
mypy app/

# Run all checks
make check
```

### Testing

```bash
# Run tests with coverage
pytest --cov=app --cov-report=html

# Run specific test categories
pytest -m "not slow"  # Skip slow tests
pytest tests/test_wells_authx.py  # Wells Fargo tests only
```

### Adding New Features

1. **Create feature branch:**
   ```bash
   git checkout -b feature/new-feature
   ```

2. **Add tests:**
   ```bash
   # Add tests in tests/ directory
   # Follow naming convention: test_*.py
   ```

3. **Run tests:**
   ```bash
   pytest tests/test_new_feature.py
   ```

4. **Check code quality:**
   ```bash
   make check
   ```

### Wells Fargo AuthX Development

```bash
# Test Wells Fargo integration
python examples/wells_authx_example.py

# Run Wells Fargo specific tests
pytest tests/test_wells_authx.py -v

# Check Wells Fargo configuration
curl http://localhost:8080/api/v1/wells-auth/info
```

## Troubleshooting

### Common Issues

#### 1. Import Errors

```bash
# Error: No module named 'ebssh_python_auth'
pip install wellsfargo_ebssh_python_auth>=1.0.71
```

#### 2. JWKS Fetch Failures

```bash
# Check network connectivity
curl -I https://your-jwks-url

# Check configuration
curl http://localhost:8080/api/v1/wells-auth/info
```

#### 3. JWT Validation Errors

```bash
# Check token format
echo "your-token" | base64 -d

# Verify claims
# Check aud, iss, exp, nbf, iat values
```

#### 4. TLS Issues

```bash
# Disable TLS for development
export TLS_ENABLED=false

# Check HTTPS configuration
curl -k https://localhost:8080/healthz
```

#### 5. Rate Limiting

```bash
# Check rate limit configuration
# Default: 100 requests per minute per client

# Adjust rate limits
export RATE_LIMIT_DEFAULT_PER_MIN=1000
```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with debug
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload --log-level debug
```

### Logs

```bash
# Check application logs
# Logs are in JSON format with correlation IDs

# Example log entry:
{
  "timestamp": "2024-01-17T10:30:00Z",
  "level": "info",
  "message": "User authenticated successfully",
  "correlation_id": "uuid-here",
  "sub": "EBSSH",
  "client_id": "test-client",
  "iss": "https://idp.example/issuer"
}
```

## Production Deployment

### Environment Setup

```bash
# Production environment variables
export LOG_LEVEL=INFO
export TLS_ENABLED=true
export ENABLE_METRICS=true
export WELLS_AUTH_ENVIRONMENT=prod
```

### Docker Deployment

```bash
# Build production image
docker build -t cop-guard:latest .

# Run with production settings
docker run -d \
  --name cop-guard \
  -p 8080:8080 \
  -e LOG_LEVEL=INFO \
  -e TLS_ENABLED=true \
  -e COP_AUDIENCE=TSIAM \
  -e ALLOWED_ISSUERS=https://idp.prod.example/issuer \
  -e JWKS_URL_PRIMARY=https://jwks.prod.example/apigee \
  -e WELLS_AUTH_ENVIRONMENT=prod \
  cop-guard:latest
```

### Health Checks

```bash
# Application health
curl http://localhost:8080/healthz

# Wells Fargo AuthX health
curl http://localhost:8080/api/v1/wells-auth/health

# Docker health check
docker inspect cop-guard --format='{{.State.Health.Status}}'
```

### Monitoring

```bash
# Enable metrics (if configured)
curl http://localhost:8080/metrics

# Check logs
docker logs cop-guard

# Monitor performance
# Use correlation IDs to trace requests
```

### Security Considerations

1. **TLS Configuration:**
   - Always use HTTPS in production
   - Configure proper TLS termination at load balancer

2. **JWKS URLs:**
   - Use production JWKS endpoints
   - Ensure network connectivity to JWKS services

3. **Rate Limiting:**
   - Adjust rate limits based on expected traffic
   - Monitor rate limit violations

4. **Logging:**
   - Ensure logs don't contain sensitive information
   - Use structured logging for monitoring

5. **Wells Fargo AuthX:**
   - Use production environment settings
   - Verify client IDs and JWKS URLs
   - Monitor authentication success rates

## Support

For issues and questions:

1. Check the troubleshooting section above
2. Review application logs with correlation IDs
3. Verify configuration settings
4. Test with sample tokens from `scripts/`
5. Check Wells Fargo AuthX health endpoint

## Additional Resources

- [README.md](README.md) - Project overview and features
- [examples/requests.http](examples/requests.http) - HTTP request examples
- [examples/wells_authx_example.py](examples/wells_authx_example.py) - Wells Fargo AuthX example
- [tests/](tests/) - Test examples and scenarios



