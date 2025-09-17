# Wells Fargo AuthX Service

A standalone FastAPI application for Wells Fargo AuthX JWT token validation using Apigee authentication.

## Features

- **Apigee-only Authentication**: Simplified to use only Wells Fargo Apigee authentication
- **JWT Token Validation**: Validates JWT tokens using Wells Fargo's AuthX service
- **FastAPI Integration**: Modern async FastAPI application with automatic API documentation
- **Health Checks**: Built-in health monitoring and configuration endpoints
- **Security Headers**: Production-ready security headers and CORS configuration

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the configuration template and update the values:

```bash
cp config.env.template .env
```

Edit `.env` with your Wells Fargo AuthX settings:

```bash
# Environment (dev, sit, prod)
WELLS_AUTH_ENVIRONMENT=dev

# Apigee Configuration
WELLS_AUTH_APIGEE_CLIENT_ID=EBSSH
WELLS_AUTH_APIGEE_JWKS_URL=https://jwks-service-dev.cfapps.wellsfargo.net/publickey/getKeys

# Authentication Settings
WELLS_AUTH_AUTO_REFRESH=true
WELLS_AUTH_VALIDATE_CLAIMS=true
WELLS_AUTH_VALIDATE_CERTIFICATE=true

# Application Settings
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=info
```

### 3. Run the Application

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## API Endpoints

### Wells AuthX Endpoints

- **POST** `/api/v1/wells-auth/validate` - Main JWT validation endpoint
- **POST** `/api/v1/wells-auth/validate/apigee` - Apigee-specific validation endpoint
- **GET** `/api/v1/wells-auth/info` - Configuration information
- **GET** `/api/v1/wells-auth/health` - Health check

### General Endpoints

- **GET** `/` - Root endpoint with service information
- **GET** `/health` - General health check
- **GET** `/config` - Configuration information (non-sensitive)
- **GET** `/docs` - Interactive API documentation (Swagger UI)
- **GET** `/redoc` - Alternative API documentation (ReDoc)

## Usage Examples

### Health Check

```bash
curl -X GET "http://localhost:8000/health"
```

### Token Validation

```bash
curl -X POST "http://localhost:8000/api/v1/wells-auth/validate" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE" \
  -H "Content-Type: application/json"
```

### Configuration Info

```bash
curl -X GET "http://localhost:8000/api/v1/wells-auth/info"
```

## Response Format

All endpoints return JSON responses in this format:

```json
{
  "code": "200",
  "status": "success",
  "provider": "apigee",
  "claims": {
    "sub": "user123",
    "client_id": "EBSSH",
    "iss": "https://apigee.wellsfargo.net",
    "aud": "your-audience",
    "scope": ["read", "write"],
    "exp": 1234567890,
    "iat": 1234567890
  }
}
```

## Error Handling

The service handles various error scenarios:

- **401 Unauthorized**: Invalid or missing JWT token
- **403 Forbidden**: Insufficient scope permissions
- **500 Internal Server Error**: Configuration or authentication service issues
- **503 Service Unavailable**: Health check failures

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `WELLS_AUTH_ENVIRONMENT` | Environment (dev/sit/prod) | `dev` |
| `WELLS_AUTH_APIGEE_CLIENT_ID` | Apigee client ID | `EBSSH` |
| `WELLS_AUTH_APIGEE_JWKS_URL` | Apigee JWKS URL | Auto-generated based on environment |
| `WELLS_AUTH_AUTO_REFRESH` | Auto-refresh JWKS keys | `true` |
| `WELLS_AUTH_VALIDATE_CLAIMS` | Validate JWT claims | `true` |
| `WELLS_AUTH_VALIDATE_CERTIFICATE` | Validate certificates | `true` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |
| `LOG_LEVEL` | Logging level | `info` |

### Default JWKS URLs

- **dev**: `https://jwks-service-dev.cfapps.wellsfargo.net/publickey/getKeys`
- **sit**: `https://jwks-service-sit.cfapps.wellsfargo.net/publickey/getKeys`
- **prod**: `https://jwks-service-prod.cfapps.wellsfargo.net/publickey/getKeys`

## Development

### Running in Development Mode

```bash
LOG_LEVEL=debug python main.py
```

### API Documentation

Once running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Production Deployment

For production deployment:

1. Set `WELLS_AUTH_ENVIRONMENT=prod`
2. Configure proper CORS origins
3. Use HTTPS with proper certificates
4. Set appropriate log levels
5. Configure monitoring and health checks

## Dependencies

- **fastapi**: Modern web framework
- **uvicorn**: ASGI server
- **pydantic**: Data validation
- **wellsfargo_ebssh_python_auth**: Wells Fargo authentication library (if available)

## License

This is a Wells Fargo internal service for authentication validation.
