"""JWKS cache implementation with background refresh and key rotation support."""

import asyncio
import json
import time
from typing import Dict, List, Optional, Set
from urllib.parse import urlparse

import requests
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.config import settings
from app.logging import get_logger

logger = get_logger(__name__)


class JWKSCache:
    """JWKS cache with TTL, background refresh, and key rotation support."""
    
    def __init__(self):
        self._cache: Dict[str, Dict] = {}
        self._cache_timestamps: Dict[str, float] = {}
        self._refresh_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        self._jwks_urls: List[str] = []
        
        # Initialize JWKS URLs
        if settings.jwks_url_primary:
            self._jwks_urls.append(settings.jwks_url_primary)
        if settings.jwks_url_secondary:
            self._jwks_urls.append(settings.jwks_url_secondary)
    
    async def start_background_refresh(self) -> None:
        """Start background refresh task."""
        if self._refresh_task is None or self._refresh_task.done():
            self._refresh_task = asyncio.create_task(self._background_refresh_loop())
            logger.info("Started JWKS background refresh task")
    
    async def stop_background_refresh(self) -> None:
        """Stop background refresh task."""
        if self._refresh_task and not self._refresh_task.done():
            self._refresh_task.cancel()
            try:
                await self._refresh_task
            except asyncio.CancelledError:
                pass
            logger.info("Stopped JWKS background refresh task")
    
    async def _background_refresh_loop(self) -> None:
        """Background task to refresh JWKS periodically."""
        while True:
            try:
                await asyncio.sleep(settings.jwks_background_refresh_sec)
                await self._refresh_all_jwks()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in background JWKS refresh", error=str(e))
    
    async def _refresh_all_jwks(self) -> None:
        """Refresh all JWKS endpoints."""
        for url in self._jwks_urls:
            try:
                await self._fetch_jwks(url, force_refresh=True)
            except Exception as e:
                logger.error("Failed to refresh JWKS", url=url, error=str(e))
    
    async def get_key(self, kid: str) -> Optional[Dict]:
        """Get a key by kid, with automatic refresh on cache miss."""
        async with self._lock:
            # Check if we have the key in cache
            for url in self._jwks_urls:
                cache_key = self._get_cache_key(url)
                if cache_key in self._cache:
                    jwks = self._cache[cache_key]
                    if 'keys' in jwks:
                        for key in jwks['keys']:
                            if key.get('kid') == kid:
                                return key
            
            # Key not found, try to refresh JWKS
            logger.warning("Key not found in cache, attempting refresh", kid=kid)
            for url in self._jwks_urls:
                try:
                    await self._fetch_jwks(url, force_refresh=True)
                    # Check again after refresh
                    cache_key = self._get_cache_key(url)
                    if cache_key in self._cache:
                        jwks = self._cache[cache_key]
                        if 'keys' in jwks:
                            for key in jwks['keys']:
                                if key.get('kid') == kid:
                                    logger.info("Key found after refresh", kid=kid, url=url)
                                    return key
                except Exception as e:
                    logger.error("Failed to refresh JWKS for key lookup", url=url, kid=kid, error=str(e))
            
            logger.error("Key not found after refresh attempt", kid=kid)
            return None
    
    async def _fetch_jwks(self, url: str, force_refresh: bool = False) -> None:
        """Fetch JWKS from URL and cache it."""
        cache_key = self._get_cache_key(url)
        current_time = time.time()
        
        # Check if we need to refresh
        if not force_refresh and cache_key in self._cache_timestamps:
            if current_time - self._cache_timestamps[cache_key] < settings.jwks_cache_ttl_sec:
                return  # Cache is still valid
        
        try:
            logger.info("Fetching JWKS", url=url)
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            jwks = response.json()
            
            # Validate JWKS structure
            if 'keys' not in jwks:
                raise ValueError("Invalid JWKS: missing 'keys' field")
            
            # Cache the JWKS
            self._cache[cache_key] = jwks
            self._cache_timestamps[cache_key] = current_time
            
            # Log key information
            key_count = len(jwks['keys'])
            kids = [key.get('kid', 'unknown') for key in jwks['keys']]
            logger.info("JWKS cached successfully", url=url, key_count=key_count, kids=kids)
            
        except requests.RequestException as e:
            logger.error("Failed to fetch JWKS", url=url, error=str(e))
            raise
        except (ValueError, KeyError) as e:
            logger.error("Invalid JWKS response", url=url, error=str(e))
            raise
    
    def _get_cache_key(self, url: str) -> str:
        """Generate cache key from URL."""
        parsed = urlparse(url)
        return f"{parsed.netloc}{parsed.path}"
    
    async def initialize(self) -> None:
        """Initialize cache by fetching all JWKS endpoints."""
        logger.info("Initializing JWKS cache", urls=self._jwks_urls)
        
        for url in self._jwks_urls:
            try:
                await self._fetch_jwks(url)
            except Exception as e:
                logger.error("Failed to initialize JWKS cache", url=url, error=str(e))
                # Don't raise here - we want to start the service even if some JWKS endpoints fail
        
        # Start background refresh
        await self.start_background_refresh()
    
    def get_cached_keys(self) -> Dict[str, List[str]]:
        """Get information about cached keys for monitoring."""
        result = {}
        for cache_key, jwks in self._cache.items():
            if 'keys' in jwks:
                kids = [key.get('kid', 'unknown') for key in jwks['keys']]
                result[cache_key] = kids
        return result


# Global JWKS cache instance
jwks_cache = JWKSCache()
