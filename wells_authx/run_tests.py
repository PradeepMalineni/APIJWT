#!/usr/bin/env python3
"""
Test runner for Wells Fargo AuthX Flask application.
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def run_basic_tests():
    """Run basic application tests."""
    print("Running basic application tests...")
    try:
        from tests.test_app import main
        return main()
    except Exception as e:
        print(f"❌ Basic tests failed: {e}")
        return 1

def run_dependency_injection_tests():
    """Run dependency injection tests."""
    print("\nRunning dependency injection tests...")
    try:
        from tests.test_dependency_injection import main
        return main()
    except Exception as e:
        print(f"❌ Dependency injection tests failed: {e}")
        return 1

def run_access_control_tests():
    """Run access control tests."""
    print("\nRunning access control tests...")
    try:
        from tests.test_access_control import main
        return main()
    except Exception as e:
        print(f"❌ Access control tests failed: {e}")
        return 1

def run_security_routes_tests():
    """Run security routes tests."""
    print("\nRunning security routes tests...")
    try:
        from tests.test_security_routes import main
        return main()
    except Exception as e:
        print(f"❌ Security routes tests failed: {e}")
        return 1

def main():
    """Run all tests."""
    print("Wells Fargo AuthX Flask Application - Test Suite")
    print("=" * 50)
    
    # Run basic tests
    basic_result = run_basic_tests()
    
    # Run dependency injection tests
    di_result = run_dependency_injection_tests()
    
    # Run access control tests
    ac_result = run_access_control_tests()
    
    # Run security routes tests
    sr_result = run_security_routes_tests()
    
    print("\n" + "=" * 50)
    if basic_result == 0 and di_result == 0 and ac_result == 0 and sr_result == 0:
        print("✅ ALL TESTS PASSED!")
        print("The Wells Fargo AuthX Flask application is ready to run.")
        print("\nTo start the application:")
        print("  python main.py")
        print("  or")
        print("  python run.py")
    else:
        print("❌ SOME TESTS FAILED!")
        print("Please check the errors above before running the application.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
