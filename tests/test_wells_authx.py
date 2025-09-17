"""Tests for Wells Fargo AuthX integration."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from wells_authx.wells_authenticator import WellsAuthenticator, AuthProvider
from wells_authx.config import WellsAuthConfig

client = TestClient(app)


@pytest.fixture
def mock_wells_claims():
    """Mock Wells Fargo JWT claims for testing."""
    return {
        "aud": "TSIAM",
        "scope": ["TSIAM-Read", "TSIAM-Write"],
        "sub": "EBSSH",
        "jti": "uuid-here",
        "nbf": 1746523720,
        "iat": 1746523720,
        "exp": 1746524020,
        "iss": "https://apigee.wellsfargo.net/issuer",
        "client_id": "EBSSH"
    }


@pytest.fixture
def mock_wells_token():
    """Mock Wells Fargo JWT token for testing."""
    return "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6InRlc3Qta2V5In0.eyJhdWQiOiJUU0lBTSIsInNjb3BlIjpbIlRTSUFNLVJlYWQiLCJUU0lBTS1Xcml0ZSJdLCJzdWIiOiJFQlNTSCIsImp0aSI6InV1aWQtaGVyZSIsIm5iZiI6MTc0NjUyMzcyMCwiaWF0IjoxNzQ2NTIzNzIwLCJleHAiOjE3NDY1MjQwMjAsImlzcyI6Imh0dHBzOi8vYXBpZ2VlLndlbGxzZmFyZ28ubmV0L2lzc3VlciIsImNsaWVudF9pZCI6IkVCU1NIIiJ9.signature"


@patch('wells_authx.wells_authenticator.wells_authenticator.authenticate_token')
async def test_wells_auth_validate_success(mock_authenticate, mock_wells_claims, mock_wells_token):
    """Test successful Wells Fargo token validation."""
    # Mock Wells Fargo authentication
    mock_authenticate.return_value = (mock_wells_claims, None)
    
    response = client.post(
        "/api/v1/wells-auth/validate",
        headers={"Authorization": f"Bearer {mock_wells_token}"}
    )
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["code"] == "200"
    assert data["status"] == "success"
    assert data["claims"] == mock_wells_claims
    assert "provider" in data


@patch('wells_authx.wells_authenticator.wells_authenticator.authenticate_token')
async def test_wells_auth_validate_apigee(mock_authenticate, mock_wells_claims, mock_wells_token):
    """Test Apigee-specific Wells Fargo token validation."""
    # Mock Wells Fargo authentication
    mock_authenticate.return_value = (mock_wells_claims, None)
    
    response = client.post(
        "/api/v1/wells-auth/validate/apigee",
        headers={"Authorization": f"Bearer {mock_wells_token}"}
    )
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["code"] == "200"
    assert data["status"] == "success"
    assert data["provider"] == "apigee"
    assert data["claims"] == mock_wells_claims


@patch('wells_authx.wells_authenticator.wells_authenticator.authenticate_token')
async def test_wells_auth_validate_pingfed(mock_authenticate, mock_wells_claims, mock_wells_token):
    """Test PingFederate-specific Wells Fargo token validation."""
    # Mock Wells Fargo authentication
    mock_authenticate.return_value = (mock_wells_claims, None)
    
    response = client.post(
        "/api/v1/wells-auth/validate/pingfed",
        headers={"Authorization": f"Bearer {mock_wells_token}"}
    )
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["code"] == "200"
    assert data["status"] == "success"
    assert data["provider"] == "pingfed"
    assert data["claims"] == mock_wells_claims


@patch('wells_authx.wells_authenticator.wells_authenticator.authenticate_token')
async def test_wells_auth_validate_failure(mock_authenticate, mock_wells_token):
    """Test Wells Fargo token validation failure."""
    # Mock Wells Fargo authentication failure
    mock_authenticate.return_value = (None, "Invalid token")
    
    response = client.post(
        "/api/v1/wells-auth/validate",
        headers={"Authorization": f"Bearer {mock_wells_token}"}
    )
    
    assert response.status_code == 401
    
    data = response.json()
    assert data["code"] == "401"
    assert data["status"] == "auth_error"
    assert "Invalid token" in data["error_message"]


@patch('wells_authx.wells_authenticator.wells_authenticator.get_provider_info')
def test_wells_auth_info(mock_get_info):
    """Test Wells Fargo AuthX info endpoint."""
    mock_get_info.return_value = {
        "provider": "auto",
        "apigee_jwks_url": "https://jwks-service-dev.cfapps.wellsfargo.net/publickey/getKeys",
        "pingfed_jwks_url": "https://cspf-sit.wellsfargo.net/pf/JWKS",
        "environment": "dev",
        "auto_refresh": True,
        "initialized": True
    }
    
    response = client.get("/api/v1/wells-auth/info")
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["code"] == "200"
    assert data["status"] == "success"
    assert "wells_authx_info" in data
    assert data["wells_authx_info"]["environment"] == "dev"


@patch('wells_authx.wells_authenticator.wells_authenticator.get_provider_info')
def test_wells_auth_health_check(mock_get_info):
    """Test Wells Fargo AuthX health check."""
    mock_get_info.return_value = {
        "provider": "auto",
        "environment": "dev",
        "initialized": True
    }
    
    response = client.get("/api/v1/wells-auth/health")
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["code"] == "200"
    assert data["status"] == "success"
    assert data["health"] == "healthy"
    assert data["wells_authx_ready"] is True


def test_wells_auth_config():
    """Test Wells Fargo AuthX configuration."""
    config = WellsAuthConfig(
        environment="dev",
        apigee_client_id="TEST_CLIENT",
        pingfed_client_id="TEST_CLIENT"
    )
    
    assert config.environment == "dev"
    assert config.apigee_client_id == "TEST_CLIENT"
    assert config.pingfed_client_id == "TEST_CLIENT"
    assert config.auto_refresh is True
    
    # Test URL generation
    apigee_url = config.get_apigee_jwks_url()
    assert "jwks-service-dev.cfapps.wellsfargo.net" in apigee_url
    
    pingfed_url = config.get_pingfed_jwks_url()
    assert "cspf-dev.wellsfargo.net" in pingfed_url


def test_wells_authenticator_initialization():
    """Test Wells Fargo authenticator initialization."""
    authenticator = WellsAuthenticator(AuthProvider.APIGEE)
    
    assert authenticator.provider == AuthProvider.APIGEE
    assert authenticator._initialized is False
    
    # Test provider info
    info = authenticator.get_provider_info()
    assert info["provider"] == "apigee"
    assert info["initialized"] is False


@pytest.mark.asyncio
async def test_wells_authenticator_auto_detection():
    """Test Wells Fargo authenticator auto-detection."""
    authenticator = WellsAuthenticator(AuthProvider.AUTO)
    
    # Mock PyAuthenticator
    with patch('ebssh_python_auth.authenticate.PyAuthenticator') as mock_py_auth:
        mock_auth_instance = MagicMock()
        mock_py_auth.return_value = mock_auth_instance
        
        # Mock successful authentication
        mock_result = MagicMock()
        mock_result.claims = {"sub": "test", "iss": "apigee"}
        mock_auth_instance.authenticate.return_value = mock_result
        
        await authenticator._initialize_authenticators()
        
        assert authenticator._initialized is True
        assert authenticator._apigee_authenticator is not None
        assert authenticator._pingfed_authenticator is not None


def test_wells_auth_missing_token():
    """Test Wells Fargo auth with missing token."""
    response = client.post("/api/v1/wells-auth/validate")
    
    assert response.status_code == 401
    
    data = response.json()
    assert data["code"] == "401"
    assert data["status"] == "auth_error"
    assert "Authorization header required" in data["error_message"]


