"""Tests for TLS functionality."""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.security.mtls import TLSValidator

client = TestClient(app)


@pytest.fixture
def mock_request():
    """Mock FastAPI request object."""
    request = MagicMock()
    request.headers = {}
    request.scope = {}
    return request


def test_tls_validator_disabled():
    """Test TLS validator when disabled."""
    validator = TLSValidator()
    validator.enabled = False
    
    # Should return None when disabled
    assert validator.get_tls_scheme(None) is None
    assert validator.get_tls_protocol(None) is None


@pytest.mark.asyncio
async def test_tls_validation_success(mock_request):
    """Test successful TLS validation."""
    validator = TLSValidator()
    validator.enabled = True
    
    # Mock HTTPS request
    mock_request.url.scheme = 'https'
    mock_request.url.hostname = 'example.com'
    mock_request.url.port = 443
    
    result = await validator.validate_tls_connection(mock_request)
    
    assert result is not None
    assert result['scheme'] == 'https'
    assert result['is_secure'] is True
    assert result['protocol'] == 'TLS 1.3'
    assert validator.get_tls_scheme(result) == 'https'
    assert validator.get_tls_protocol(result) == 'TLS 1.3'


@pytest.mark.asyncio
async def test_tls_validation_http_request(mock_request):
    """Test TLS validation with HTTP request (should fail)."""
    validator = TLSValidator()
    validator.enabled = True
    
    # Mock HTTP request (not HTTPS)
    mock_request.url.scheme = 'http'
    mock_request.url.hostname = 'example.com'
    mock_request.url.port = 80
    
    with pytest.raises(Exception):  # Should raise HTTPException
        await validator.validate_tls_connection(mock_request)


def test_tls_info_extraction():
    """Test TLS info extraction."""
    validator = TLSValidator()
    
    # Mock request with HTTPS
    request = MagicMock()
    request.url.scheme = 'https'
    request.url.hostname = 'example.com'
    request.url.port = 443
    
    result = validator._get_tls_info(request)
    
    assert result['scheme'] == 'https'
    assert result['hostname'] == 'example.com'
    assert result['port'] == 443
    assert result['is_secure'] is True
    assert result['protocol'] == 'TLS 1.3'


def test_tls_scheme_getters():
    """Test TLS scheme and protocol getters."""
    validator = TLSValidator()
    
    # Test with valid TLS info
    tls_info = {
        'scheme': 'https',
        'protocol': 'TLS 1.3',
        'is_secure': True
    }
    
    assert validator.get_tls_scheme(tls_info) == 'https'
    assert validator.get_tls_protocol(tls_info) == 'TLS 1.3'
    
    # Test with None
    assert validator.get_tls_scheme(None) is None
    assert validator.get_tls_protocol(None) is None
