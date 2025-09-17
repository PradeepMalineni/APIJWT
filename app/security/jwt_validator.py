"""JWT validator with RS256 support and comprehensive claims validation."""

import base64
import json
import time
from typing import Dict, List, Optional, Tuple

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.config import settings
from app.logging import get_logger
from app.security.jwks_cache import jwks_cache

logger = get_logger(__name__)


class JWTValidationError(Exception):
    """Custom exception for JWT validation errors."""
    pass


class JWTValidator:
    """JWT validator with RS256 support and claims validation."""
    
    def __init__(self):
        self.algorithm = "RS256"
    
    async def validate_jwt(self, token: str) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Validate JWT token and return claims or error.
        
        Args:
            token: JWT token string
            
        Returns:
            Tuple of (claims_dict, error_message)
        """
        try:
            # Parse JWT header to get kid
            header = self._parse_jwt_header(token)
            kid = header.get('kid')
            if not kid:
                return None, "Token validation failed: Missing 'kid' in header"
            
            # Get the public key
            key_data = await jwks_cache.get_key(kid)
            if not key_data:
                return None, f"Token validation failed: Key '{kid}' not found"
            
            # Convert JWK to PEM format
            public_key = self._jwk_to_pem(key_data)
            
            # Decode and verify JWT
            try:
                claims = jwt.decode(
                    token,
                    public_key,
                    algorithms=[self.algorithm],
                    audience=settings.cop_audience,
                    issuer=settings.allowed_issuers,
                    options={
                        "verify_signature": True,
                        "verify_exp": True,
                        "verify_nbf": True,
                        "verify_iat": True,
                        "verify_aud": True,
                        "verify_iss": True,
                    }
                )
            except jwt.ExpiredSignatureError:
                return None, "Token validation failed: Token has expired"
            except jwt.InvalidAudienceError:
                return None, "Token validation failed: Invalid audience"
            except jwt.InvalidIssuerError:
                return None, "Token validation failed: Invalid issuer"
            except jwt.InvalidTokenError as e:
                return None, f"Token validation failed: {str(e)}"
            
            # Additional claims validation
            validation_error = self._validate_claims(claims)
            if validation_error:
                return None, f"Token validation failed: {validation_error}"
            
            # Log successful validation
            logger.info(
                "JWT validation successful",
                kid=kid,
                sub=claims.get('sub'),
                aud=claims.get('aud'),
                iss=claims.get('iss'),
                scope=claims.get('scope', [])
            )
            
            return claims, None
            
        except Exception as e:
            logger.error("Unexpected error during JWT validation", error=str(e))
            return None, f"Token validation failed: {str(e)}"
    
    def _parse_jwt_header(self, token: str) -> Dict:
        """Parse JWT header without verification."""
        try:
            # Split token into parts
            parts = token.split('.')
            if len(parts) != 3:
                raise ValueError("Invalid JWT format")
            
            # Decode header
            header_b64 = parts[0]
            # Add padding if needed
            header_b64 += '=' * (4 - len(header_b64) % 4)
            header_json = base64.urlsafe_b64decode(header_b64)
            header = json.loads(header_json)
            
            return header
            
        except Exception as e:
            raise JWTValidationError(f"Failed to parse JWT header: {str(e)}")
    
    def _jwk_to_pem(self, jwk: Dict) -> str:
        """Convert JWK to PEM format."""
        try:
            # Extract key components
            n = base64.urlsafe_b64decode(jwk['n'] + '==')
            e = base64.urlsafe_b64decode(jwk['e'] + '==')
            
            # Convert to integers
            n_int = int.from_bytes(n, 'big')
            e_int = int.from_bytes(e, 'big')
            
            # Create RSA public key
            public_key = rsa.RSAPublicNumbers(e_int, n_int).public_key()
            
            # Serialize to PEM
            pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            return pem.decode('utf-8')
            
        except Exception as e:
            raise JWTValidationError(f"Failed to convert JWK to PEM: {str(e)}")
    
    def _validate_claims(self, claims: Dict) -> Optional[str]:
        """Validate JWT claims with additional checks."""
        current_time = time.time()
        
        # Check clock skew for iat
        if 'iat' in claims:
            iat = claims['iat']
            if abs(current_time - iat) > settings.max_clock_skew_sec:
                return f"Issued at time drift exceeds {settings.max_clock_skew_sec} seconds"
        
        # Check clock skew for exp
        if 'exp' in claims:
            exp = claims['exp']
            if abs(current_time - exp) > settings.max_clock_skew_sec:
                return f"Expiration time drift exceeds {settings.max_clock_skew_sec} seconds"
        
        # Check clock skew for nbf
        if 'nbf' in claims:
            nbf = claims['nbf']
            if abs(current_time - nbf) > settings.max_clock_skew_sec:
                return f"Not before time drift exceeds {settings.max_clock_skew_sec} seconds"
        
        # Validate required claims
        required_claims = ['sub', 'aud', 'iss']
        for claim in required_claims:
            if claim not in claims:
                return f"Missing required claim: {claim}"
        
        # Validate audience
        if claims['aud'] != settings.cop_audience:
            return f"Invalid audience: expected '{settings.cop_audience}', got '{claims['aud']}'"
        
        # Validate issuer
        if claims['iss'] not in settings.allowed_issuers:
            return f"Invalid issuer: '{claims['iss']}' not in allowed issuers"
        
        return None
    
    def extract_scope(self, claims: Dict) -> List[str]:
        """Extract scope from claims."""
        scope = claims.get('scope', [])
        if isinstance(scope, str):
            # Handle space-separated scopes
            return [s.strip() for s in scope.split() if s.strip()]
        elif isinstance(scope, list):
            return scope
        else:
            return []
    
    def has_scope(self, claims: Dict, required_scope: str) -> bool:
        """Check if claims contain required scope."""
        scopes = self.extract_scope(claims)
        return required_scope in scopes
    
    def has_any_scope(self, claims: Dict, required_scopes: List[str]) -> bool:
        """Check if claims contain any of the required scopes."""
        scopes = self.extract_scope(claims)
        return any(scope in scopes for scope in required_scopes)


# Global JWT validator instance
jwt_validator = JWTValidator()
