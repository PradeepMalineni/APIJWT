"""Tests for successful JWT validation."""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture
def mock_jwt_claims():
    """Mock JWT claims for testing."""
    return {
        "aud": "TSIAM",
        "scope": ["TSIAM-Read", "TSIAM-Write"],
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
    return "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6InRlc3Qta2V5In0.eyJhdWQiOiJUU0lBTSIsInNjb3BlIjpbIlRTSUFNLVJlYWQiLCJUU0lBTS1Xcml0ZSJdLCJzdWIiOiJFQlNTSCIsImp0aSI6InV1aWQtaGVyZSIsIm5iZiI6MTc0NjUyMzcyMCwiaWF0IjoxNzQ2NTIzNzIwLCJleHAiOjE3NDY1MjQwMjAsImlzcyI6Imh0dHBzOi8vaWRwLmV4YW1wbGUvaXNzdWVyIiwiY2xpZW50X2lkIjoidGVzdC1jbGllbnQifQ.signature"


@patch('app.security.jwt_validator.jwt_validator.validate_jwt')
@patch('app.security.jwks_cache.jwks_cache.get_key')
async def test_validate_token_success(mock_get_key, mock_validate_jwt, mock_jwt_claims, mock_jwt_token):
    """Test successful JWT validation."""
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
    
    response = client.post(
        "/api/v1/auth/validate",
        headers={"Authorization": f"Bearer {mock_jwt_token}"}
    )
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["code"] == "200"
    assert data["status"] == "success"
    assert data["claims"] == mock_jwt_claims


@patch('app.security.jwt_validator.jwt_validator.validate_jwt')
@patch('app.security.jwks_cache.jwks_cache.get_key')
async def test_validate_token_missing_auth_header(mock_get_key, mock_validate_jwt):
    """Test JWT validation with missing authorization header."""
    response = client.post("/api/v1/auth/validate")
    
    assert response.status_code == 401
    
    data = response.json()
    assert data["code"] == "401"
    assert data["status"] == "auth_error"
    assert "Authorization header required" in data["error_message"]


@patch('app.security.jwt_validator.jwt_validator.validate_jwt')
@patch('app.security.jwks_cache.jwks_cache.get_key')
async def test_validate_token_invalid_format(mock_get_key, mock_validate_jwt):
    """Test JWT validation with invalid token format."""
    response = client.post(
        "/api/v1/auth/validate",
        headers={"Authorization": "InvalidFormat token"}
    )
    
    assert response.status_code == 401
    
    data = response.json()
    assert data["code"] == "401"
    assert data["status"] == "auth_error"
