"""Tests for expired JWT validation."""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture
def mock_jwt_token():
    """Mock expired JWT token for testing."""
    return "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6InRlc3Qta2V5In0.eyJhdWQiOiJUU0lBTSIsInNjb3BlIjpbIlRTSUFNLVJlYWQiXSwic3ViIjoiRUJTU0giLCJqdGkiOiJ1dWlkLWhlcmUiLCJuYmYiOjE3NDY1MjM3MjAsImlhdCI6MTc0NjUyMzcyMCwiZXhwIjoxNzQ2NTIzNzIwLCJpc3MiOiJodHRwczovL2lkcC5leGFtcGxlL2lzc3VlciJ9.signature"


@patch('app.security.jwt_validator.jwt_validator.validate_jwt')
@patch('app.security.jwks_cache.jwks_cache.get_key')
async def test_validate_expired_token(mock_get_key, mock_validate_jwt, mock_jwt_token):
    """Test JWT validation with expired token."""
    # Mock JWKS key
    mock_get_key.return_value = {
        "kty": "RSA",
        "kid": "test-key",
        "use": "sig",
        "n": "test-n",
        "e": "AQAB"
    }
    
    # Mock JWT validation returning expired error
    mock_validate_jwt.return_value = (None, "Token validation failed: Token has expired")
    
    response = client.post(
        "/api/v1/auth/validate",
        headers={"Authorization": f"Bearer {mock_jwt_token}"}
    )
    
    assert response.status_code == 401
    
    data = response.json()
    assert data["code"] == "401"
    assert data["status"] == "auth_error"
    assert data["error_message"] == "Token validation failed: Token has expired"


@patch('app.security.jwt_validator.jwt_validator.validate_jwt')
@patch('app.security.jwks_cache.jwks_cache.get_key')
async def test_validate_invalid_audience(mock_get_key, mock_validate_jwt, mock_jwt_token):
    """Test JWT validation with invalid audience."""
    # Mock JWKS key
    mock_get_key.return_value = {
        "kty": "RSA",
        "kid": "test-key",
        "use": "sig",
        "n": "test-n",
        "e": "AQAB"
    }
    
    # Mock JWT validation returning invalid audience error
    mock_validate_jwt.return_value = (None, "Token validation failed: Invalid audience")
    
    response = client.post(
        "/api/v1/auth/validate",
        headers={"Authorization": f"Bearer {mock_jwt_token}"}
    )
    
    assert response.status_code == 401
    
    data = response.json()
    assert data["code"] == "401"
    assert data["status"] == "auth_error"
    assert data["error_message"] == "Token validation failed: Invalid audience"


@patch('app.security.jwt_validator.jwt_validator.validate_jwt')
@patch('app.security.jwks_cache.jwks_cache.get_key')
async def test_validate_invalid_issuer(mock_get_key, mock_validate_jwt, mock_jwt_token):
    """Test JWT validation with invalid issuer."""
    # Mock JWKS key
    mock_get_key.return_value = {
        "kty": "RSA",
        "kid": "test-key",
        "use": "sig",
        "n": "test-n",
        "e": "AQAB"
    }
    
    # Mock JWT validation returning invalid issuer error
    mock_validate_jwt.return_value = (None, "Token validation failed: Invalid issuer")
    
    response = client.post(
        "/api/v1/auth/validate",
        headers={"Authorization": f"Bearer {mock_jwt_token}"}
    )
    
    assert response.status_code == 401
    
    data = response.json()
    assert data["code"] == "401"
    assert data["status"] == "auth_error"
    assert data["error_message"] == "Token validation failed: Invalid issuer"
