#!/usr/bin/env python3
"""
Test script to verify the Wells Fargo AuthX Flask application can start.
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    
    try:
        from config import WellsAuthConfig
        print("✅ Config module imported successfully")
    except Exception as e:
        print(f"❌ Config import failed: {e}")
        return False
    
    try:
        from ..security import WellsAuthenticator
        print("✅ WellsAuthenticator imported successfully")
    except Exception as e:
        print(f"❌ WellsAuthenticator import failed: {e}")
        return False
    
    try:
        from ..security import get_wells_authenticated_user, require_wells_scope
        print("✅ Flask decorators imported successfully")
    except Exception as e:
        print(f"❌ Flask decorators import failed: {e}")
        return False
    
    try:
        from routes import bp
        print("✅ Flask Blueprint imported successfully")
    except Exception as e:
        print(f"❌ Flask Blueprint import failed: {e}")
        return False
    
    return True

def test_config():
    """Test configuration."""
    print("\nTesting configuration...")
    
    try:
        from ..config import WellsAuthConfig
        config = WellsAuthConfig()
        
        print(f"Environment: {config.environment}")
        print(f"Client ID: {config.apigee_client_id}")
        print(f"JWKS URL: {config.get_apigee_jwks_url()}")
        print(f"Auto Refresh: {config.auto_refresh}")
        
        print("✅ Configuration loaded successfully")
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_authenticator():
    """Test authenticator initialization."""
    print("\nTesting authenticator...")
    
    try:
        from ..security import WellsAuthenticator
        from ..config import WellsAuthConfig
        
        config = WellsAuthConfig()
        authenticator = WellsAuthenticator(config)
        
        provider_info = authenticator.get_provider_info()
        print(f"Provider: {provider_info.get('provider')}")
        print(f"Environment: {provider_info.get('environment')}")
        print(f"Initialized: {provider_info.get('initialized')}")
        
        print("✅ Authenticator created successfully")
        return True
    except Exception as e:
        print(f"❌ Authenticator test failed: {e}")
        return False

def test_flask_app():
    """Test Flask app creation."""
    print("\nTesting Flask app...")
    
    try:
        from main import app
        
        print(f"App name: {app.name}")
        print(f"Number of routes: {len(app.url_map._rules)}")
        
        # Test route registration
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append(f"{rule.methods} {rule.rule}")
        
        print("Registered routes:")
        for route in routes:
            print(f"  {route}")
        
        print("✅ Flask app created successfully")
        return True
    except Exception as e:
        print(f"❌ Flask app test failed: {e}")
        return False

def test_decorators():
    """Test Flask decorators."""
    print("\nTesting Flask decorators...")
    
    try:
        from ..security import get_wells_authenticated_user, require_wells_scope
        
        # Test that decorators are callable
        if callable(get_wells_authenticated_user) and callable(require_wells_scope):
            print("✅ Flask decorators are callable")
        else:
            print("❌ Flask decorators are not callable")
            return False
        
        print("✅ Flask decorators imported successfully")
        return True
    except Exception as e:
        print(f"❌ Flask decorators test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("Wells Fargo AuthX Flask Application Test")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_config,
        test_authenticator,
        test_flask_app,
        test_decorators
    ]
    
    all_passed = True
    for test in tests:
        try:
            if not test():
                all_passed = False
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            all_passed = False
    
    print("\n" + "=" * 40)
    if all_passed:
        print("✅ ALL TESTS PASSED!")
        print("The Wells Fargo AuthX Flask application is ready to run.")
        print("\nTo start the application:")
        print("  python main.py")
        print("  or")
        print("  python run.py")
        print("\nAPI endpoints will be available at:")
        print("  http://localhost:8000/")
        print("  http://localhost:8000/health")
        print("  http://localhost:8000/api/v1/wells-auth/validate")
    else:
        print("❌ SOME TESTS FAILED!")
        print("Please check the errors above before running the application.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)