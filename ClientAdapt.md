# Wells AuthX Client Configuration Guide

## Overview
The Wells AuthX module provides authentication services for Wells Fargo's Apigee and PingFederate providers. It supports JWT token validation with automatic provider detection.

## 1. Environment Configuration

First, you need to configure your environment variables. Create a `.env` file or set these environment variables:

```bash
# Wells AuthX Configuration
WELLS_AUTH_ENVIRONMENT=dev  # Options: dev, sit, prod
WELLS_AUTH_APIGEE_CLIENT_ID=EBSSH
WELLS_AUTH_PINGFED_CLIENT_ID=EBSSH
WELLS_AUTH_AUTO_REFRESH=true
WELLS_AUTH_VALIDATE_CLAIMS=true
WELLS_AUTH_VALIDATE_CERTIFICATE=true

# Optional: Override default JWKS URLs
WELLS_AUTH_APIGEE_JWKS_URL=https://your-custom-apigee-jwks-url
WELLS_AUTH_PINGFED_JWKS_URL=https://your-custom-pingfed-jwks-url
```

## 2. Default JWKS URLs by Environment

The system automatically uses these URLs based on your environment:

### Development (dev):
- **Apigee**: `https://jwks-service-dev.cfapps.wellsfargo.net/publickey/getKeys`
- **PingFederate**: `https://cspf-dev.wellsfargo.net/pf/JWKS`

### SIT:
- **Apigee**: `https://jwks-service-sit.cfapps.wellsfargo.net/publickey/getKeys`
- **PingFederate**: `https://cspf-sit.wellsfargo.net/pf/JWKS`

### Production (prod):
- **Apigee**: `https://jwks-service-prod.cfapps.wellsfargo.net/publickey/getKeys`
- **PingFederate**: `https://cspf-prod.wellsfargo.net/pf/JWKS`

## 3. API Endpoints

The Wells AuthX module provides these endpoints:

### 3.1 General Token Validation
```http
POST /wells-auth/validate
Authorization: Bearer <your-jwt-token>
```

### 3.2 Apigee-Specific Validation
```http
POST /wells-auth/validate/apigee
Authorization: Bearer <your-jwt-token>
```

### 3.3 PingFederate-Specific Validation
```http
POST /wells-auth/validate/pingfed
Authorization: Bearer <your-jwt-token>
```

### 3.4 Configuration Information
```http
GET /wells-auth/info
```

### 3.5 Health Check
```http
GET /wells-auth/health
```

## 4. Client Implementation Examples

### 4.1 Python Client Example

```python
import requests
import json

class WellsAuthXClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def validate_token(self, provider: str = 'auto') -> dict:
        """Validate JWT token using Wells AuthX"""
        if provider == 'apigee':
            endpoint = '/wells-auth/validate/apigee'
        elif provider == 'pingfed':
            endpoint = '/wells-auth/validate/pingfed'
        else:
            endpoint = '/wells-auth/validate'
        
        response = requests.post(
            f"{self.base_url}{endpoint}",
            headers=self.headers
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Authentication failed: {response.text}")
    
    def get_auth_info(self) -> dict:
        """Get Wells AuthX configuration information"""
        response = requests.get(f"{self.base_url}/wells-auth/info")
        return response.json()
    
    def health_check(self) -> dict:
        """Check Wells AuthX health status"""
        response = requests.get(f"{self.base_url}/wells-auth/health")
        return response.json()

# Usage example
client = WellsAuthXClient(
    base_url="http://localhost:8080",
    token="your-jwt-token-here"
)

try:
    # Validate token (auto-detect provider)
    result = client.validate_token()
    print("Authentication successful!")
    print(f"Provider: {result['provider']}")
    print(f"Claims: {result['claims']}")
    
    # Get configuration info
    info = client.get_auth_info()
    print(f"Environment: {info['wells_authx_info']['environment']}")
    
except Exception as e:
    print(f"Error: {e}")
```

### 4.2 cURL Examples

```bash
# Validate token (auto-detect provider)
curl -X POST "http://localhost:8080/wells-auth/validate" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"

# Validate with specific provider
curl -X POST "http://localhost:8080/wells-auth/validate/apigee" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"

# Get configuration info
curl -X GET "http://localhost:8080/wells-auth/info"

# Health check
curl -X GET "http://localhost:8080/wells-auth/health"
```

### 4.3 JavaScript/Node.js Client Example

```javascript
class WellsAuthXClient {
    constructor(baseUrl, token) {
        this.baseUrl = baseUrl.replace(/\/$/, '');
        this.token = token;
        this.headers = {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        };
    }

    async validateToken(provider = 'auto') {
        let endpoint;
        switch (provider) {
            case 'apigee':
                endpoint = '/wells-auth/validate/apigee';
                break;
            case 'pingfed':
                endpoint = '/wells-auth/validate/pingfed';
                break;
            default:
                endpoint = '/wells-auth/validate';
        }

        const response = await fetch(`${this.baseUrl}${endpoint}`, {
            method: 'POST',
            headers: this.headers
        });

        if (response.ok) {
            return await response.json();
        } else {
            throw new Error(`Authentication failed: ${await response.text()}`);
        }
    }

    async getAuthInfo() {
        const response = await fetch(`${this.baseUrl}/wells-auth/info`);
        return await response.json();
    }

    async healthCheck() {
        const response = await fetch(`${this.baseUrl}/wells-auth/health`);
        return await response.json();
    }
}

// Usage example
const client = new WellsAuthXClient(
    'http://localhost:8080',
    'your-jwt-token-here'
);

try {
    const result = await client.validateToken();
    console.log('Authentication successful!');
    console.log(`Provider: ${result.provider}`);
    console.log(`Claims:`, result.claims);
} catch (error) {
    console.error('Error:', error.message);
}
```

## 5. JWT Token Requirements

Your JWT token should contain these standard claims:

- **`sub`**: Subject (user/client identifier)
- **`iss`**: Issuer (should match Wells Fargo issuer)
- **`aud`**: Audience (typically "TSIAM")
- **`exp`**: Expiration time
- **`iat`**: Issued at time
- **`client_id`**: Client identifier (typically "EBSSH")
- **`scope`**: Array of scopes (e.g., ["TSIAM-Read", "TSIAM-Write"])

### Example JWT Token Structure:
```json
{
  "sub": "EBSSH",
  "client_id": "EBSSH",
  "iss": "https://apigee.wellsfargo.net/issuer",
  "aud": "TSIAM",
  "scope": ["TSIAM-Read", "TSIAM-Write"],
  "exp": 1746524020,
  "iat": 1746523720,
  "jti": "uuid-here"
}
```

## 6. Response Format

### Successful Authentication Response:
```json
{
  "code": "200",
  "status": "success",
  "provider": "apigee",
  "claims": {
    "sub": "EBSSH",
    "client_id": "EBSSH",
    "iss": "https://apigee.wellsfargo.net/issuer",
    "aud": "TSIAM",
    "scope": ["TSIAM-Read", "TSIAM-Write"],
    "exp": 1746524020,
    "iat": 1746523720
  }
}
```

### Error Response:
```json
{
  "code": "401",
  "status": "auth_error",
  "error_message": "Authorization header required"
}
```

## 7. Error Handling

### Common Error Codes:
- **401**: Unauthorized - Invalid or missing token
- **403**: Forbidden - Insufficient scope
- **500**: Internal Server Error - Service unavailable
- **503**: Service Unavailable - Health check failed

### Error Response Examples:
```json
{
  "code": "401",
  "status": "auth_error",
  "error_message": "Token has expired"
}
```

```json
{
  "code": "403",
  "status": "auth_error",
  "error_message": "Insufficient scope. Required: TSIAM-Write"
}
```

## 8. Integration with Main Application

To integrate Wells AuthX with your main application, you need to include the Wells AuthX router in your FastAPI app:

```python
# In your main.py or app initialization
from wells_authx.routes import router as wells_authx_router

app.include_router(wells_authx_router, prefix="/api/v1", tags=["wells-authx"])
```

### Complete Integration Example:
```python
from fastapi import FastAPI
from wells_authx.routes import router as wells_authx_router
from wells_authx.config import WellsAuthConfig

# Initialize Wells AuthX configuration
wells_config = WellsAuthConfig(
    environment="dev",
    apigee_client_id="EBSSH",
    pingfed_client_id="EBSSH",
    auto_refresh=True
)

app = FastAPI(title="Your API with Wells AuthX")

# Include Wells AuthX routes
app.include_router(wells_authx_router, prefix="/api/v1", tags=["wells-authx"])

# Your other routes...
@app.get("/api/v1/protected")
async def protected_endpoint():
    return {"message": "This endpoint is protected by Wells AuthX"}
```

## 9. Dependencies

Make sure you have the required dependencies installed:

```bash
pip install wellsfargo_ebssh_python_auth>=1.0.71
pip install fastapi
pip install pydantic
pip install pyjwt
pip install requests  # For client examples
```

### requirements.txt:
```
wellsfargo_ebssh_python_auth>=1.0.71
fastapi>=0.68.0
pydantic>=1.8.0
pyjwt>=2.0.0
requests>=2.25.0
uvicorn>=0.15.0
```

## 10. Security Considerations

### 10.1 TLS Requirements
- All JWKS URLs must use HTTPS
- Client connections should use TLS 1.2 or higher
- Certificate validation is enabled by default

### 10.2 Token Security
- JWT tokens are validated for signature, expiration, and claims
- Tokens should be transmitted over secure channels only
- Store tokens securely and never log them

### 10.3 Rate Limiting
- Built-in rate limiting middleware prevents abuse
- Default limit: 100 requests per minute per client
- Configure appropriate limits for your use case

### 10.4 Monitoring and Logging
- All requests include correlation IDs for tracking
- Authentication events are logged with appropriate detail
- Health checks monitor service availability

## 11. Testing

### 11.1 Unit Testing Example
```python
import pytest
from wells_authx.wells_authenticator import WellsAuthenticator, AuthProvider

@pytest.mark.asyncio
async def test_wells_authx_authentication():
    authenticator = WellsAuthenticator(AuthProvider.AUTO)
    
    # Test with valid token
    claims, error = await authenticator.authenticate_token("valid-jwt-token")
    assert error is None
    assert claims is not None
    assert claims.get('sub') == 'EBSSH'
```

### 11.2 Integration Testing
```python
import requests

def test_wells_authx_endpoint():
    response = requests.post(
        "http://localhost:8080/wells-auth/validate",
        headers={"Authorization": "Bearer test-token"}
    )
    assert response.status_code in [200, 401]  # 401 expected for test token
```

## 12. Troubleshooting

### 12.1 Common Issues

**Issue**: `PyAuthenticator not available`
**Solution**: Install the Wells Fargo authentication package:
```bash
pip install wellsfargo_ebssh_python_auth>=1.0.71
```

**Issue**: `JWKS URL validation failed`
**Solution**: Ensure JWKS URLs use HTTPS and are accessible:
```bash
curl -I https://jwks-service-dev.cfapps.wellsfargo.net/publickey/getKeys
```

**Issue**: `Token validation failed`
**Solution**: Check token format and claims:
- Ensure token is properly formatted JWT
- Verify required claims are present
- Check token expiration

### 12.2 Debug Mode
Enable debug logging to troubleshoot issues:
```bash
export WELLS_AUTH_LOG_LEVEL=DEBUG
```

### 12.3 Health Check
Monitor service health:
```bash
curl http://localhost:8080/wells-auth/health
```

## 13. Best Practices

1. **Environment Configuration**: Use environment-specific configurations
2. **Error Handling**: Implement proper error handling and retry logic
3. **Token Management**: Implement token refresh mechanisms
4. **Monitoring**: Set up monitoring and alerting for authentication failures
5. **Security**: Follow security best practices for token storage and transmission
6. **Testing**: Implement comprehensive testing for authentication flows
7. **Documentation**: Keep client documentation updated with API changes

## 14. Support and Resources

- **Wells Fargo AuthX Documentation**: Internal Wells Fargo documentation
- **PyAuthenticator Package**: `wellsfargo_ebssh_python_auth` package documentation
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **JWT.io**: https://jwt.io/ for JWT token debugging

---

*This guide provides comprehensive information for integrating with the Wells AuthX API. For additional support or questions, please refer to the Wells Fargo internal documentation or contact the development team.*
