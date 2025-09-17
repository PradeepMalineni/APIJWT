#!/usr/bin/env python3
"""
Simple script to run the Wells Fargo AuthX service.
"""

import os
import sys
import uvicorn
from pathlib import Path

def main():
    """Run the Wells Fargo AuthX service."""
    
    # Get configuration from environment variables
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    reload = log_level == "debug"
    
    print(f"Starting Wells Fargo AuthX Service...")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Log Level: {log_level}")
    print(f"Reload: {reload}")
    print(f"API Documentation: http://{host}:{port}/docs")
    print("-" * 50)
    
    try:
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            log_level=log_level,
            reload=reload,
            access_log=True
        )
    except KeyboardInterrupt:
        print("\nShutting down Wells Fargo AuthX Service...")
    except Exception as e:
        print(f"Error starting service: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
