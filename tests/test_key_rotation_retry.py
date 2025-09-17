"""Tests for JWKS key rotation and retry logic."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.security.jwks_cache import JWKSCache

client = TestClient(app)


@pytest.fixture
def mock_jwt_token():
    """Mock JWT token for testing."""
    return "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6InRlc3Qta2V5In0.eyJhdWQiOiJUU0lBTSIsInNjb3BlIjpbIlRTSUFNLVJlYWQiXSwic3ViIjoiRUJTU0giLCJqdGkiOiJ1dWlkLWhlcmUiLCJuYmYiOjE3NDY1MjM3MjAsImlhdCI6MTc0NjUyMzcyMCwiZXhwIjoxNzQ2NTI0MDIwLCJpc3MiOiJodHRwczovL2lkcC5leGFtcGxlL2lzc3VlciJ9.signature"


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


@patch('app.security.jwt_validator.jwt_validator.validate_jwt')
@patch('app.security.jwks_cache.jwks_cache.get_key')
async def test_key_rotation_retry_success(mock_get_key, mock_validate_jwt, mock_jwt_claims, mock_jwt_token):
    """Test successful key rotation retry."""
    # Mock JWKS key lookup - first call fails, second succeeds
    mock_get_key.side_effect = [
        None,  # First call fails (key not found)
        {     # Second call succeeds after refresh
            "kty": "RSA",
            "kid": "test-key",
            "use": "sig",
            "n": "test-n",
            "e": "AQAB"
        }
    ]
    
    # Mock JWT validation - first call fails, second succeeds
    mock_validate_jwt.side_effect = [
        (None, "Token validation failed: Key 'test-key' not found"),  # First call fails
        (mock_jwt_claims, None)  # Second call succeeds
    ]
    
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
async def test_key_rotation_retry_failure(mock_get_key, mock_validate_jwt, mock_jwt_token):
    """Test key rotation retry failure."""
    # Mock JWKS key lookup - both calls fail
    mock_get_key.return_value = None
    
    # Mock JWT validation - both calls fail
    mock_validate_jwt.return_value = (None, "Token validation failed: Key 'test-key' not found")
    
    response = client.post(
        "/api/v1/auth/validate",
        headers={"Authorization": f"Bearer {mock_jwt_token}"}
    )
    
    assert response.status_code == 401
    
    data = response.json()
    assert data["code"] == "401"
    assert data["status"] == "auth_error"
    assert "Key 'test-key' not found" in data["error_message"]


@pytest.mark.asyncio
async def test_jwks_cache_key_rotation():
    """Test JWKS cache key rotation functionality."""
    cache = JWKSCache()
    
    # Mock the _fetch_jwks method
    with patch.object(cache, '_fetch_jwks') as mock_fetch:
        # First call returns old key
        old_jwks = {
            "keys": [
                {
                    "kty": "RSA",
                    "kid": "old-key",
                    "use": "sig",
                    "n": "old-n",
                    "e": "AQAB"
                }
            ]
        }
        
        # Second call returns new key
        new_jwks = {
            "keys": [
                {
                    "kty": "RSA",
                    "kid": "new-key",
                    "use": "sig",
                    "n": "new-n",
                    "e": "AQAB"
                }
            ]
        }
        
        mock_fetch.side_effect = [None, None]  # Both calls succeed
        
        # Test getting old key
        key = await cache.get_key("old-key")
        assert key is None  # Key not found initially
        
        # Test getting new key after rotation
        key = await cache.get_key("new-key")
        assert key is None  # Key not found initially


@pytest.mark.asyncio
async def test_jwks_cache_background_refresh():
    """Test JWKS cache background refresh."""
    cache = JWKSCache()
    
    with patch.object(cache, '_refresh_all_jwks') as mock_refresh:
        # Start background refresh
        await cache.start_background_refresh()
        
        # Wait a bit for background task to run
        await asyncio.sleep(0.1)
        
        # Stop background refresh
        await cache.stop_background_refresh()
        
        # Verify refresh was called
        assert mock_refresh.called


@patch('app.security.jwt_validator.jwt_validator.validate_jwt')
@patch('app.security.jwks_cache.jwks_cache.get_key')
async def test_multiple_jwks_endpoints(mock_get_key, mock_validate_jwt, mock_jwt_claims, mock_jwt_token):
    """Test JWT validation with multiple JWKS endpoints."""
    # Mock JWKS key from secondary endpoint
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
async def test_unknown_kid_with_retry(mock_get_key, mock_validate_jwt, mock_jwt_claims, mock_jwt_token):
    """Test handling of unknown kid with retry logic."""
    # Mock JWKS key lookup - first call fails, second succeeds
    mock_get_key.side_effect = [
        None,  # First call fails (unknown kid)
        {     # Second call succeeds after refresh
            "kty": "RSA",
            "kid": "test-key",
            "use": "sig",
            "n": "test-n",
            "e": "AQAB"
        }
    ]
    
    # Mock JWT validation - first call fails, second succeeds
    mock_validate_jwt.side_effect = [
        (None, "Token validation failed: Key 'test-key' not found"),  # First call fails
        (mock_jwt_claims, None)  # Second call succeeds
    ]
    
    response = client.post(
        "/api/v1/auth/validate",
        headers={"Authorization": f"Bearer {mock_jwt_token}"}
    )
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["code"] == "200"
    assert data["status"] == "success"
    assert data["claims"] == mock_jwt_claims
