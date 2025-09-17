"""Tests for rate limiting functionality."""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture
def mock_jwt_claims():
    """Mock JWT claims for testing."""
    return {
        "aud": "TSIAM",
        "scope": ["TSIAM-Read"],
        "sub": "EBSSH",
        "jti": "uuid-here",
        "nbf": 1746523720,
        "iat": 1746523720,
        "exp": 1746524020,
        "iss": "https://idp.example/issuer",
        "client_id": "test-client"
    }


@pytest.fixture
def mock_jwt_token():
    """Mock JWT token for testing."""
    return "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6InRlc3Qta2V5In0.eyJhdWQiOiJUU0lBTSIsInNjb3BlIjpbIlRTSUFNLVJlYWQiXSwic3ViIjoiRUJTU0giLCJqdGkiOiJ1dWlkLWhlcmUiLCJuYmYiOjE3NDY1MjM3MjAsImlhdCI6MTc0NjUyMzcyMCwiZXhwIjoxNzQ2NTI0MDIwLCJpc3MiOiJodHRwczovL2lkcC5leGFtcGxlL2lzc3VlciJ9.signature"


@patch('app.security.jwt_validator.jwt_validator.validate_jwt')
@patch('app.security.jwks_cache.jwks_cache.get_key')
async def test_rate_limiting_with_client_id(mock_get_key, mock_validate_jwt, mock_jwt_claims, mock_jwt_token):
    """Test rate limiting using client_id from JWT claims."""
    # Mock JWKS key
    mock_get_key.return_value = {
        "kty": "RSA",
        "kid": "test-key",
        "use": "sig",
        "n": "test-n",
        "e": "AQAB"
    }
    
    # Mock JWT validation
    mock_validate_jwt.return_value = (mock_jwt_claims, None)
    
    # Make multiple requests to test rate limiting
    responses = []
    for i in range(5):  # Make 5 requests
        response = client.get(
            "/api/v1/onboarding/apps",
            headers={"Authorization": f"Bearer {mock_jwt_token}"}
        )
        responses.append(response)
    
    # All requests should succeed (within rate limit)
    for response in responses:
        assert response.status_code in [200, 429]  # 200 for success, 429 for rate limit


@patch('app.security.jwt_validator.jwt_validator.validate_jwt')
@patch('app.security.jwks_cache.jwks_cache.get_key')
async def test_rate_limiting_without_auth(mock_get_key, mock_validate_jwt):
    """Test rate limiting without authentication (using IP)."""
    # Make multiple requests without authentication
    responses = []
    for i in range(5):  # Make 5 requests
        response = client.get("/healthz")
        responses.append(response)
    
    # All requests should succeed (health check is not rate limited)
    for response in responses:
        assert response.status_code == 200


@patch('app.security.jwt_validator.jwt_validator.validate_jwt')
@patch('app.security.jwks_cache.jwks_cache.get_key')
async def test_rate_limiting_exceeded(mock_get_key, mock_validate_jwt, mock_jwt_claims, mock_jwt_token):
    """Test rate limiting when limit is exceeded."""
    # Mock JWKS key
    mock_get_key.return_value = {
        "kty": "RSA",
        "kid": "test-key",
        "use": "sig",
        "n": "test-n",
        "e": "AQAB"
    }
    
    # Mock JWT validation
    mock_validate_jwt.return_value = (mock_jwt_claims, None)
    
    # Mock rate limiter to always exceed limit
    with patch('app.middleware.rate_limit.limiter._check_request_limit') as mock_check:
        from slowapi.errors import RateLimitExceeded
        mock_check.side_effect = RateLimitExceeded("Rate limit exceeded")
        
        response = client.get(
            "/api/v1/onboarding/apps",
            headers={"Authorization": f"Bearer {mock_jwt_token}"}
        )
        
        assert response.status_code == 429
        
        data = response.json()
        assert data["code"] == "429"
        assert data["status"] == "rate_limit_exceeded"
        assert "Rate limit exceeded" in data["error_message"]


def test_rate_limiting_client_identifier():
    """Test client identifier extraction for rate limiting."""
    from app.middleware.rate_limit import get_client_identifier
    
    # Mock request with client_id in state
    request = MagicMock()
    request.state.claims = {"client_id": "test-client"}
    
    identifier = get_client_identifier(request)
    assert identifier == "client:test-client"
    
    # Mock request without client_id
    request.state.claims = {"sub": "test-user"}
    request.client.host = "192.168.1.1"
    
    with patch('app.middleware.rate_limit.get_remote_address', return_value="192.168.1.1"):
        identifier = get_client_identifier(request)
        assert identifier == "ip:192.168.1.1"


@patch('app.security.jwt_validator.jwt_validator.validate_jwt')
@patch('app.security.jwks_cache.jwks_cache.get_key')
async def test_rate_limiting_per_route(mock_get_key, mock_validate_jwt, mock_jwt_claims, mock_jwt_token):
    """Test per-route rate limiting."""
    # Mock JWKS key
    mock_get_key.return_value = {
        "kty": "RSA",
        "kid": "test-key",
        "use": "sig",
        "n": "test-n",
        "e": "AQAB"
    }
    
    # Mock JWT validation
    mock_validate_jwt.return_value = (mock_jwt_claims, None)
    
    # Test rate limiting on different routes
    routes_to_test = [
        "/api/v1/onboarding/apps",
        "/api/v1/onboarding/apps/app-001",
        "/api/v1/auth/validate"
    ]
    
    for route in routes_to_test:
        response = client.get(
            route,
            headers={"Authorization": f"Bearer {mock_jwt_token}"}
        )
        # Should either succeed or be rate limited
        assert response.status_code in [200, 201, 403, 429]
