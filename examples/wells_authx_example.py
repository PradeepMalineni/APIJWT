#!/usr/bin/env python3
"""
Example script demonstrating Wells Fargo AuthX integration.

This script shows how to use the Wells Fargo AuthX authenticator
directly without the FastAPI web service.
"""

import asyncio
import os
from wells_authx.wells_authenticator import WellsAuthenticator, AuthProvider
from wells_authx.config import WellsAuthConfig


async def main():
    """Demonstrate Wells Fargo AuthX authentication."""
    
    # Configure Wells Fargo AuthX
    config = WellsAuthConfig(
        environment="dev",
        apigee_client_id="EBSSH",
        pingfed_client_id="EBSSH",
        auto_refresh=True
    )
    
    print("Wells Fargo AuthX Configuration:")
    print(f"  Environment: {config.environment}")
    print(f"  Apigee JWKS URL: {config.get_apigee_jwks_url()}")
    print(f"  PingFederate JWKS URL: {config.get_pingfed_jwks_url()}")
    print(f"  Auto-refresh: {config.auto_refresh}")
    print()
    
    # Initialize authenticator
    authenticator = WellsAuthenticator(AuthProvider.AUTO)
    
    # Get provider info
    info = authenticator.get_provider_info()
    print("Authenticator Info:")
    for key, value in info.items():
        print(f"  {key}: {value}")
    print()
    
    # Example token (this would be a real JWT token in practice)
    example_token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6InRlc3Qta2V5In0.eyJhdWQiOiJUU0lBTSIsInNjb3BlIjpbIlRTSUFNLVJlYWQiLCJUU0lBTS1Xcml0ZSJdLCJzdWIiOiJFQlNTSCIsImp0aSI6InV1aWQtaGVyZSIsIm5iZiI6MTc0NjUyMzcyMCwiaWF0IjoxNzQ2NTIzNzIwLCJleHAiOjE3NDY1MjQwMjAsImlzcyI6Imh0dHBzOi8vYXBpZ2VlLndlbGxzZmFyZ28ubmV0L2lzc3VlciIsImNsaWVudF9pZCI6IkVCU1NIIiJ9.signature"
    
    print("Testing token authentication...")
    print(f"Token: {example_token[:50]}...")
    print()
    
    try:
        # Authenticate token
        claims, error = await authenticator.authenticate_token(example_token)
        
        if error:
            print(f"Authentication failed: {error}")
        else:
            print("Authentication successful!")
            print("Claims:")
            for key, value in claims.items():
                print(f"  {key}: {value}")
                
    except Exception as e:
        print(f"Error during authentication: {e}")
        print("Note: This example requires the wellsfargo_ebssh_python_auth package to be installed.")
        print("Install it with: pip install wellsfargo_ebssh_python_auth>=1.0.71")


if __name__ == "__main__":
    asyncio.run(main())


