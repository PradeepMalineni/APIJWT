# COP Guard API Protection Layer

A production-ready API protection layer for securing COP (Consumer Onboarding Platform) APIs called by an Integrated Developer Portal (IDP).

## Features

- **TLS 1.3 Support**: Modern TLS encryption with optional mTLS (client certificate) support
- **OAuth2/JWT Validation**: RS256 JWT validation using JWKS with automatic key rotation
- **Claims & Scope Enforcement**: Comprehensive validation of aud/iss/exp/nbf/iat/scope claims
- **Rate Limiting**: Configurable rate limiting with client-based identification
- **Structured Audit Logging**: JSON logging with correlation IDs for observability
- **Least Privilege Authorization**: Route-level scope enforcement
- **Security Headers**: Production-ready security headers
- **Container Ready**: Docker support with health checks

## Quick Start

### Prerequisites

- Python 3.11+
- Docker (optional)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd cop-guard
```

2. Install dependencies:
```bash
pip install -e ".[dev,test]"
```

3. Set environment variables:
```bash
export PORT=8080
export COP_AUDIENCE=TSIAM
export ALLOWED_ISSUERS=https://idp.example/issuer,https://ping.example/issuer
export JWKS_URL_PRIMARY=https://jwks.example/apigee
export JWKS_URL_SECONDARY=https://jwks.example/ping
export JWKS_CACHE_TTL_SEC=900
export JWKS_BACKGROUND_REFRESH_SEC=600
export MAX_CLOCK_SKEW_SEC=120
export MTLS_REQUIRED=false
export RATE_LIMIT_DEFAULT_PER_MIN=100
export LOG_LEVEL=INFO
```

4. Run the application:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

### Docker

```bash
# Build the image
docker build -t cop-guard .

# Run the container
docker run -p 8080:8080 \
  -e COP_AUDIENCE=TSIAM \
  -e ALLOWED_ISSUERS=https://idp.example/issuer \
  -e JWKS_URL_PRIMARY=https://jwks.example/apigee \
  cop-guard
```

## API Endpoints

### Public Endpoints

- `GET /healthz` - Health check (no authentication required)
- `GET /health` - Alternative health check
- `GET /` - Root endpoint with service information

### Authentication Endpoints

- `POST /api/v1/auth/validate` - Validate JWT token

### Protected Endpoints

- `GET /api/v1/onboarding/apps` - List applications (requires `TSIAM-Read` scope)
- `POST /api/v1/onboarding/apps` - Create application (requires `TSIAM-Write` scope)
- `GET /api/v1/onboarding/apps/{app_id}` - Get application (requires `TSIAM-Read` scope)
- `PUT /api/v1/onboarding/apps/{app_id}` - Update application (requires `TSIAM-Write` scope)

## Configuration

All configuration is done via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Server port | `8080` |
| `COP_AUDIENCE` | Expected JWT audience | `TSIAM` |
| `ALLOWED_ISSUERS` | Comma-separated list of allowed issuers | Required |
| `JWKS_URL_PRIMARY` | Primary JWKS endpoint URL | Required |
| `JWKS_URL_SECONDARY` | Secondary JWKS endpoint URL | Optional |
| `JWKS_CACHE_TTL_SEC` | JWKS cache TTL in seconds | `900` |
| `JWKS_BACKGROUND_REFRESH_SEC` | Background refresh interval | `600` |
| `MAX_CLOCK_SKEW_SEC` | Maximum clock skew tolerance | `120` |
| `MTLS_REQUIRED` | Enable mTLS validation | `false` |
| `RATE_LIMIT_DEFAULT_PER_MIN` | Default rate limit per minute | `100` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `ENABLE_METRICS` | Enable metrics endpoint | `false` |

## Usage Examples

### Health Check

```bash
curl http://localhost:8080/healthz
```

Response:
```json
{
  "status": "healthy",
  "service": "cop-guard",
  "version": "1.0.0"
}
```

### JWT Validation

```bash
curl -X POST http://localhost:8080/api/v1/auth/validate \
  -H "Authorization: Bearer <your-jwt-token>"
```

Success Response:
```json
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

Error Response:
```json
{
  "code": "401",
  "status": "auth_error",
  "error_message": "Token validation failed: Token has expired."
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

## Security Features

### JWT Validation

- **Algorithm**: RS256 (RSA with SHA-256)
- **Key Rotation**: Automatic JWKS refresh with retry logic
- **Claims Validation**: Comprehensive validation of all required claims
- **Clock Skew**: Configurable tolerance for time differences

### mTLS Support

When `MTLS_REQUIRED=true`, the service validates client certificates:

- Extracts certificates from `X-Client-Cert` header (proxy mode)
- Validates certificate chain and expiration
- Exposes certificate information in request context

### Rate Limiting

- **Client-based**: Uses `client_id` from JWT claims when available
- **IP-based**: Falls back to IP address for unauthenticated requests
- **Configurable**: Per-route rate limits can be customized
- **Headers**: Includes rate limit information in response headers

### Security Headers

All responses include security headers:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_health.py
```

### Linting and Type Checking

```bash
# Run ruff linter
ruff check app/ tests/

# Run mypy type checker
mypy app/

# Format code
ruff format app/ tests/
```

### Code Quality

The project uses:

- **ruff**: Fast Python linter and formatter
- **mypy**: Static type checking
- **pytest**: Testing framework
- **pytest-cov**: Coverage reporting

## Monitoring and Observability

### Logging

Structured JSON logging with:

- Correlation IDs for request tracking
- Request/response information
- Authentication and authorization decisions
- Performance metrics
- Error details

### Metrics

Optional Prometheus metrics endpoint at `/metrics` (when enabled).

### Health Checks

- `/healthz`: Basic health check
- `/health`: Alternative health check
- Docker health check included

## Deployment

### Production Considerations

1. **Secrets Management**: Use proper secret management for JWKS URLs and other sensitive config
2. **TLS Termination**: Configure proper TLS termination at load balancer/proxy level
3. **Rate Limiting**: Adjust rate limits based on expected traffic patterns
4. **Monitoring**: Set up monitoring and alerting for the service
5. **Scaling**: Use multiple workers for high availability

### Environment-Specific Configuration

#### Development
```bash
export LOG_LEVEL=DEBUG
export ENABLE_METRICS=true
```

#### Production
```bash
export LOG_LEVEL=INFO
export ENABLE_METRICS=true
export MTLS_REQUIRED=true
```

## Troubleshooting

### Common Issues

1. **JWKS Fetch Failures**: Check network connectivity and JWKS URL validity
2. **JWT Validation Errors**: Verify token format and claims
3. **Rate Limiting**: Check rate limit configuration and client identification
4. **mTLS Issues**: Verify certificate format and validation logic

### Debug Mode

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
```

### Health Check Failures

Check service logs and verify:
- JWKS endpoints are accessible
- Configuration is correct
- Dependencies are available

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the logs for error details
# APIJWT
