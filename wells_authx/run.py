#!/usr/bin/env python3
"""
Simple script to run the Wells Fargo AuthX Flask service.
"""

import os
import sys
from main import app

def main():
    """Run the Wells Fargo AuthX Flask service."""
    
    # Get configuration from environment variables
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    debug = os.getenv("LOG_LEVEL", "info").lower() == "debug"
    
    print(f"Starting Wells Fargo AuthX Flask Service...")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Debug: {debug}")
    print(f"API Endpoints: http://{host}:{port}/")
    print("-" * 50)
    
    try:
        app.run(
            host=host,
            port=port,
            debug=debug
        )
    except KeyboardInterrupt:
        print("\nShutting down Wells Fargo AuthX Flask Service...")
    except Exception as e:
        print(f"Error starting service: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()