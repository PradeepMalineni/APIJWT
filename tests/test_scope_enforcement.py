"""Tests for scope enforcement in protected routes."""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture
def mock_jwt_claims_read():
    """Mock JWT claims with read scope only."""
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
def mock_jwt_claims_write():
    """Mock JWT claims with write scope."""
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
def mock_jwt_claims_no_scope():
    """Mock JWT claims with no scopes."""
    return {
        "aud": "TSIAM",
        "scope": [],
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
async def test_get_onboarding_apps_with_read_scope(mock_get_key, mock_validate_jwt, mock_jwt_claims_read, mock_jwt_token):
    """Test GET /onboarding/apps with TSIAM-Read scope."""
    # Mock JWKS key
    mock_get_key.return_value = {
        "kty": "RSA",
        "kid": "test-key",
        "use": "sig",
        "n": "test-n",
        "e": "AQAB"
    }
    
    # Mock JWT validation
    mock_validate_jwt.return_value = (mock_jwt_claims_read, None)
    
    response = client.get(
        "/api/v1/onboarding/apps",
        headers={"Authorization": f"Bearer {mock_jwt_token}"}
    )
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["code"] == "200"
    assert data["status"] == "success"
    assert "applications" in data["data"]


@patch('app.security.jwt_validator.jwt_validator.validate_jwt')
@patch('app.security.jwks_cache.jwks_cache.get_key')
async def test_get_onboarding_apps_without_read_scope(mock_get_key, mock_validate_jwt, mock_jwt_claims_no_scope, mock_jwt_token):
    """Test GET /onboarding/apps without TSIAM-Read scope."""
    # Mock JWKS key
    mock_get_key.return_value = {
        "kty": "RSA",
        "kid": "test-key",
        "use": "sig",
        "n": "test-n",
        "e": "AQAB"
    }
    
    # Mock JWT validation
    mock_validate_jwt.return_value = (mock_jwt_claims_no_scope, None)
    
    response = client.get(
        "/api/v1/onboarding/apps",
        headers={"Authorization": f"Bearer {mock_jwt_token}"}
    )
    
    assert response.status_code == 403
    
    data = response.json()
    assert data["code"] == "403"
    assert data["status"] == "auth_error"
    assert "Insufficient scope" in data["error_message"]
    assert "TSIAM-Read" in data["error_message"]


@patch('app.security.jwt_validator.jwt_validator.validate_jwt')
@patch('app.security.jwks_cache.jwks_cache.get_key')
async def test_post_onboarding_apps_with_write_scope(mock_get_key, mock_validate_jwt, mock_jwt_claims_write, mock_jwt_token):
    """Test POST /onboarding/apps with TSIAM-Write scope."""
    # Mock JWKS key
    mock_get_key.return_value = {
        "kty": "RSA",
        "kid": "test-key",
        "use": "sig",
        "n": "test-n",
        "e": "AQAB"
    }
    
    # Mock JWT validation
    mock_validate_jwt.return_value = (mock_jwt_claims_write, None)
    
    app_data = {
        "name": "Test Application",
        "description": "A test application"
    }
    
    response = client.post(
        "/api/v1/onboarding/apps",
        headers={"Authorization": f"Bearer {mock_jwt_token}"},
        json=app_data
    )
    
    assert response.status_code == 201
    
    data = response.json()
    assert data["code"] == "201"
    assert data["status"] == "success"
    assert "application" in data["data"]


@patch('app.security.jwt_validator.jwt_validator.validate_jwt')
@patch('app.security.jwks_cache.jwks_cache.get_key')
async def test_post_onboarding_apps_without_write_scope(mock_get_key, mock_validate_jwt, mock_jwt_claims_read, mock_jwt_token):
    """Test POST /onboarding/apps without TSIAM-Write scope."""
    # Mock JWKS key
    mock_get_key.return_value = {
        "kty": "RSA",
        "kid": "test-key",
        "use": "sig",
        "n": "test-n",
        "e": "AQAB"
    }
    
    # Mock JWT validation
    mock_validate_jwt.return_value = (mock_jwt_claims_read, None)
    
    app_data = {
        "name": "Test Application",
        "description": "A test application"
    }
    
    response = client.post(
        "/api/v1/onboarding/apps",
        headers={"Authorization": f"Bearer {mock_jwt_token}"},
        json=app_data
    )
    
    assert response.status_code == 403
    
    data = response.json()
    assert data["code"] == "403"
    assert data["status"] == "auth_error"
    assert "Insufficient scope" in data["error_message"]
    assert "TSIAM-Write" in data["error_message"]


@patch('app.security.jwt_validator.jwt_validator.validate_jwt')
@patch('app.security.jwks_cache.jwks_cache.get_key')
async def test_get_specific_onboarding_app_with_read_scope(mock_get_key, mock_validate_jwt, mock_jwt_claims_read, mock_jwt_token):
    """Test GET /onboarding/apps/{app_id} with TSIAM-Read scope."""
    # Mock JWKS key
    mock_get_key.return_value = {
        "kty": "RSA",
        "kid": "test-key",
        "use": "sig",
        "n": "test-n",
        "e": "AQAB"
    }
    
    # Mock JWT validation
    mock_validate_jwt.return_value = (mock_jwt_claims_read, None)
    
    response = client.get(
        "/api/v1/onboarding/apps/app-001",
        headers={"Authorization": f"Bearer {mock_jwt_token}"}
    )
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["code"] == "200"
    assert data["status"] == "success"
    assert "application" in data["data"]
    assert data["data"]["application"]["id"] == "app-001"


@patch('app.security.jwt_validator.jwt_validator.validate_jwt')
@patch('app.security.jwks_cache.jwks_cache.get_key')
async def test_put_onboarding_app_with_write_scope(mock_get_key, mock_validate_jwt, mock_jwt_claims_write, mock_jwt_token):
    """Test PUT /onboarding/apps/{app_id} with TSIAM-Write scope."""
    # Mock JWKS key
    mock_get_key.return_value = {
        "kty": "RSA",
        "kid": "test-key",
        "use": "sig",
        "n": "test-n",
        "e": "AQAB"
    }
    
    # Mock JWT validation
    mock_validate_jwt.return_value = (mock_jwt_claims_write, None)
    
    app_data = {
        "name": "Updated Application",
        "status": "active"
    }
    
    response = client.put(
        "/api/v1/onboarding/apps/app-001",
        headers={"Authorization": f"Bearer {mock_jwt_token}"},
        json=app_data
    )
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["code"] == "200"
    assert data["status"] == "success"
    assert "application" in data["data"]
    assert data["data"]["application"]["id"] == "app-001"
    assert data["data"]["application"]["name"] == "Updated Application"
