"""Tests for JWT validation with wrong audience."""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture
def mock_jwt_token():
    """Mock JWT token with wrong audience for testing."""
    return "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6InRlc3Qta2V5In0.eyJhdWQiOiJXUk9ORy1BVURJRU5DRSIsInNjb3BlIjpbIlRTSUFNLVJlYWQiXSwic3ViIjoiRUJTU0giLCJqdGkiOiJ1dWlkLWhlcmUiLCJuYmYiOjE3NDY1MjM3MjAsImlhdCI6MTc0NjUyMzcyMCwiZXhwIjoxNzQ2NTI0MDIwLCJpc3MiOiJodHRwczovL2lkcC5leGFtcGxlL2lzc3VlciJ9.signature"


@patch('app.security.jwt_validator.jwt_validator.validate_jwt')
@patch('app.security.jwks_cache.jwks_cache.get_key')
async def test_validate_wrong_audience(mock_get_key, mock_validate_jwt, mock_jwt_token):
    """Test JWT validation with wrong audience."""
    # Mock JWKS key
    mock_get_key.return_value = {
        "kty": "RSA",
        "kid": "test-key",
        "use": "sig",
        "n": "test-n",
        "e": "AQAB"
    }
    
    # Mock JWT validation returning wrong audience error
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
async def test_validate_missing_audience_claim(mock_get_key, mock_validate_jwt, mock_jwt_token):
    """Test JWT validation with missing audience claim."""
    # Mock JWKS key
    mock_get_key.return_value = {
        "kty": "RSA",
        "kid": "test-key",
        "use": "sig",
        "n": "test-n",
        "e": "AQAB"
    }
    
    # Mock JWT validation returning missing audience error
    mock_validate_jwt.return_value = (None, "Token validation failed: Missing required claim: aud")
    
    response = client.post(
        "/api/v1/auth/validate",
        headers={"Authorization": f"Bearer {mock_jwt_token}"}
    )
    
    assert response.status_code == 401
    
    data = response.json()
    assert data["code"] == "401"
    assert data["status"] == "auth_error"
    assert "Missing required claim: aud" in data["error_message"]


@patch('app.security.jwt_validator.jwt_validator.validate_jwt')
@patch('app.security.jwks_cache.jwks_cache.get_key')
async def test_validate_malformed_token(mock_get_key, mock_validate_jwt):
    """Test JWT validation with malformed token."""
    # Mock JWKS key
    mock_get_key.return_value = {
        "kty": "RSA",
        "kid": "test-key",
        "use": "sig",
        "n": "test-n",
        "e": "AQAB"
    }
    
    # Mock JWT validation returning malformed token error
    mock_validate_jwt.return_value = (None, "Token validation failed: Invalid token format")
    
    response = client.post(
        "/api/v1/auth/validate",
        headers={"Authorization": "Bearer malformed.token.here"}
    )
    
    assert response.status_code == 401
    
    data = response.json()
    assert data["code"] == "401"
    assert data["status"] == "auth_error"
    assert "Invalid token format" in data["error_message"]
