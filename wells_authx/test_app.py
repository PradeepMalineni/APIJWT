#!/usr/bin/env python3
"""
Test script to verify the Wells Fargo AuthX application can start.
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
        from wells_authenticator import WellsAuthenticator
        print("✅ WellsAuthenticator imported successfully")
    except Exception as e:
        print(f"❌ WellsAuthenticator import failed: {e}")
        return False
    
    try:
        from deps import get_wells_authenticated_user
        print("✅ Dependencies imported successfully")
    except Exception as e:
        print(f"❌ Dependencies import failed: {e}")
        return False
    
    try:
        from routes import router
        print("✅ Routes imported successfully")
    except Exception as e:
        print(f"❌ Routes import failed: {e}")
        return False
    
    return True

def test_config():
    """Test configuration."""
    print("\nTesting configuration...")
    
    try:
        from config import wells_auth_config
        
        print(f"Environment: {wells_auth_config.environment}")
        print(f"Client ID: {wells_auth_config.apigee_client_id}")
        print(f"JWKS URL: {wells_auth_config.get_apigee_jwks_url()}")
        print(f"Auto Refresh: {wells_auth_config.auto_refresh}")
        
        print("✅ Configuration loaded successfully")
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_authenticator():
    """Test authenticator initialization."""
    print("\nTesting authenticator...")
    
    try:
        from wells_authenticator import wells_authenticator
        
        provider_info = wells_authenticator.get_provider_info()
        print(f"Provider: {provider_info.get('provider')}")
        print(f"Environment: {provider_info.get('environment')}")
        print(f"Initialized: {provider_info.get('initialized')}")
        
        print("✅ Authenticator created successfully")
        return True
    except Exception as e:
        print(f"❌ Authenticator test failed: {e}")
        return False

def test_fastapi_app():
    """Test FastAPI app creation."""
    print("\nTesting FastAPI app...")
    
    try:
        from main import app
        
        print(f"App title: {app.title}")
        print(f"App version: {app.version}")
        print(f"Number of routes: {len(app.routes)}")
        
        print("✅ FastAPI app created successfully")
        return True
    except Exception as e:
        print(f"❌ FastAPI app test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("Wells Fargo AuthX Application Test")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_config,
        test_authenticator,
        test_fastapi_app
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
        print("The Wells Fargo AuthX application is ready to run.")
        print("\nTo start the application:")
        print("  python main.py")
        print("  or")
        print("  python run.py")
        print("\nAPI Documentation will be available at:")
        print("  http://localhost:8000/docs")
    else:
        print("❌ SOME TESTS FAILED!")
        print("Please check the errors above before running the application.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
