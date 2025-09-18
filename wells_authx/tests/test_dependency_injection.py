"""Test file demonstrating dependency injection and improved architecture."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, Optional, Tuple

from ..security import DependencyContainer, WellsAuthenticatorProtocol, WellsAuthenticator
from ..config import WellsAuthConfig


class MockWellsAuthenticator:
    """Mock authenticator for testing."""
    
    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail
        self._initialized = True
    
    async def authenticate_token(
        self, 
        token: str, 
        client_id: Optional[str] = None
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Mock authenticate token method."""
        if self.should_fail:
            return None, "Mock authentication failed"
        
        # Return mock claims
        claims = {
            "sub": "test_user_123",
            "client_id": "test_client",
            "iss": "https://test.wellsfargo.com",
            "aud": "test_audience",
            "scope": ["read", "write"]
        }
        return claims, None
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Mock get provider info method."""
        return {
            "provider": "apigee",
            "apigee_jwks_url": "https://test.jwks.url",
            "environment": "test",
            "auto_refresh": True,
            "initialized": self._initialized
        }


class TestDependencyInjection:
    """Test dependency injection container."""
    
    def test_container_initialization(self):
        """Test container initialization."""
        container = DependencyContainer()
        
        # Test that authenticator is not set initially
        with pytest.raises(RuntimeError, match="Authenticator not configured"):
            container.get_authenticator()
        
        # Test that config is not set initially
        with pytest.raises(RuntimeError, match="Configuration not set"):
            container.get_config()
    
    def test_container_set_authenticator(self):
        """Test setting authenticator in container."""
        container = DependencyContainer()
        mock_authenticator = MockWellsAuthenticator()
        
        container.set_authenticator(mock_authenticator)
        retrieved_authenticator = container.get_authenticator()
        
        assert retrieved_authenticator is mock_authenticator
    
    def test_container_set_config(self):
        """Test setting config in container."""
        container = DependencyContainer()
        config = WellsAuthConfig(environment="test")
        
        container.set_config(config)
        retrieved_config = container.get_config()
        
        assert retrieved_config is config
        assert retrieved_config.environment == "test"
    
    def test_container_event_loop_management(self):
        """Test event loop management in container."""
        container = DependencyContainer()
        
        # Get event loop
        loop1 = container.get_event_loop()
        assert loop1 is not None
        
        # Get same event loop again
        loop2 = container.get_event_loop()
        assert loop1 is loop2
        
        # Test with closed loop
        loop1.close()
        loop3 = container.get_event_loop()
        assert loop3 is not None
        assert loop3 is not loop1


class TestWellsAuthenticator:
    """Test Wells authenticator with dependency injection."""
    
    def test_authenticator_initialization(self):
        """Test authenticator initialization with config."""
        config = WellsAuthConfig(environment="test")
        authenticator = WellsAuthenticator(config)
        
        assert authenticator._config is config
        assert authenticator._initialized is False
    
    def test_authenticator_without_config(self):
        """Test authenticator initialization without config."""
        authenticator = WellsAuthenticator()
        
        assert authenticator._config is not None
        assert isinstance(authenticator._config, WellsAuthConfig)
    
    @pytest.mark.asyncio
    async def test_authenticator_initialization_success(self):
        """Test successful authenticator initialization."""
        config = WellsAuthConfig(environment="test")
        authenticator = WellsAuthenticator(config)
        
        with patch('wells_authenticator.PyAuthenticator') as mock_py_auth:
            mock_instance = Mock()
            mock_py_auth.return_value = mock_instance
            
            await authenticator._initialize_authenticator()
            
            assert authenticator._initialized is True
            assert authenticator._apigee_authenticator is mock_instance
            mock_py_auth.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_authenticator_initialization_import_error(self):
        """Test authenticator initialization with import error."""
        config = WellsAuthConfig(environment="test")
        authenticator = WellsAuthenticator(config)
        
        with patch('wells_authenticator.PyAuthenticator', side_effect=ImportError("Module not found")):
            with pytest.raises(RuntimeError, match="PyAuthenticator not available"):
                await authenticator._initialize_authenticator()
    
    def test_authenticator_get_provider_info(self):
        """Test getting provider info."""
        config = WellsAuthConfig(environment="test")
        authenticator = WellsAuthenticator(config)
        
        info = authenticator.get_provider_info()
        
        assert info["provider"] == "apigee"
        assert info["environment"] == "test"
        assert info["initialized"] is False


class TestIntegration:
    """Integration tests for the complete system."""
    
    def test_full_integration(self):
        """Test full integration with dependency injection."""
        # Create container
        container = DependencyContainer()
        
        # Create and configure dependencies
        config = WellsAuthConfig(environment="test")
        authenticator = WellsAuthenticator(config)
        
        # Set dependencies in container
        container.set_config(config)
        container.set_authenticator(authenticator)
        
        # Verify dependencies are properly set
        retrieved_config = container.get_config()
        retrieved_authenticator = container.get_authenticator()
        
        assert retrieved_config is config
        assert retrieved_authenticator is authenticator
        
        # Test provider info
        provider_info = retrieved_authenticator.get_provider_info()
        assert provider_info["environment"] == "test"
        assert provider_info["provider"] == "apigee"


if __name__ == "__main__":
    # Run basic tests
    print("Running dependency injection tests...")
    
    # Test container
    container = DependencyContainer()
    print("✓ Container initialization works")
    
    # Test authenticator
    config = WellsAuthConfig(environment="test")
    authenticator = WellsAuthenticator(config)
    print("✓ Authenticator initialization works")
    
    # Test integration
    container.set_config(config)
    container.set_authenticator(authenticator)
    print("✓ Dependency injection integration works")
    
    # Test provider info
    info = authenticator.get_provider_info()
    print(f"✓ Provider info: {info}")
    
    print("\nAll basic tests passed! 🎉")
    print("\nTo run full test suite:")
    print("pip install pytest pytest-asyncio")
    print("pytest test_dependency_injection.py -v")
