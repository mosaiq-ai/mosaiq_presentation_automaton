"""
Caching service for improved performance.

This module provides caching functionality for the application,
including in-memory caching and file-based persistent caching.
"""

import asyncio
import functools
import hashlib
import inspect
import json
import os
import pickle
import time
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, TypeVar, Union, cast

from loguru import logger


class CacheType(str, Enum):
    """Type of cache to use."""
    MEMORY = "memory"
    FILE = "file"
    BOTH = "both"


T = TypeVar('T')


class CacheService:
    """Service for caching data to improve performance."""
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize the caching service.
        
        Args:
            cache_dir: Directory for file-based cache storage
        """
        # Set up memory cache
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        
        # Set up file cache
        if cache_dir is None:
            # Default to project cache directory
            base_dir = Path(__file__).parent.parent.parent.parent
            self._cache_dir = str(base_dir / "cache")
        else:
            self._cache_dir = cache_dir
        
        # Create cache directory if it doesn't exist
        os.makedirs(self._cache_dir, exist_ok=True)
        
        logger.info(f"Cache service initialized with cache directory: {self._cache_dir}")
    
    async def get(
        self, 
        namespace: str, 
        key: str, 
        default: Any = None,
        cache_type: CacheType = CacheType.BOTH
    ) -> Any:
        """
        Get a value from the cache.
        
        Args:
            namespace: Cache namespace
            key: Cache key
            default: Default value if key not found
            cache_type: Type of cache to check
            
        Returns:
            Cached value or default if not found
        """
        # Check memory cache first
        if cache_type in (CacheType.MEMORY, CacheType.BOTH):
            value = self._get_from_memory(namespace, key)
            if value is not None:
                return value
        
        # Check file cache if not found in memory
        if cache_type in (CacheType.FILE, CacheType.BOTH):
            value = await self._get_from_file(namespace, key)
            if value is not None:
                # Update memory cache with file value
                if cache_type == CacheType.BOTH:
                    self._set_in_memory(namespace, key, value)
                return value
        
        return default
    
    async def set(
        self, 
        namespace: str, 
        key: str, 
        value: Any,
        expire: Optional[int] = None,
        cache_type: CacheType = CacheType.BOTH
    ) -> None:
        """
        Set a value in the cache.
        
        Args:
            namespace: Cache namespace
            key: Cache key
            value: Value to cache
            expire: Expiration time in seconds (optional)
            cache_type: Type of cache to use
        """
        # Set in memory cache
        if cache_type in (CacheType.MEMORY, CacheType.BOTH):
            self._set_in_memory(namespace, key, value, expire)
        
        # Set in file cache
        if cache_type in (CacheType.FILE, CacheType.BOTH):
            await self._set_in_file(namespace, key, value)
    
    async def delete(
        self, 
        namespace: str, 
        key: str,
        cache_type: CacheType = CacheType.BOTH
    ) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            namespace: Cache namespace
            key: Cache key
            cache_type: Type of cache to use
            
        Returns:
            True if the key was deleted, False otherwise
        """
        memory_deleted = False
        file_deleted = False
        
        # Delete from memory cache
        if cache_type in (CacheType.MEMORY, CacheType.BOTH):
            memory_deleted = self._delete_from_memory(namespace, key)
        
        # Delete from file cache
        if cache_type in (CacheType.FILE, CacheType.BOTH):
            file_deleted = await self._delete_from_file(namespace, key)
        
        return memory_deleted or file_deleted
    
    async def clear(
        self, 
        namespace: Optional[str] = None,
        cache_type: CacheType = CacheType.BOTH
    ) -> None:
        """
        Clear the cache for a namespace or all namespaces.
        
        Args:
            namespace: Cache namespace to clear (all if None)
            cache_type: Type of cache to clear
        """
        # Clear memory cache
        if cache_type in (CacheType.MEMORY, CacheType.BOTH):
            if namespace is None:
                self._memory_cache.clear()
            elif namespace in self._memory_cache:
                del self._memory_cache[namespace]
        
        # Clear file cache
        if cache_type in (CacheType.FILE, CacheType.BOTH):
            if namespace is None:
                # Clear all cache files
                for ns_dir in os.listdir(self._cache_dir):
                    ns_path = os.path.join(self._cache_dir, ns_dir)
                    if os.path.isdir(ns_path):
                        for cache_file in os.listdir(ns_path):
                            os.remove(os.path.join(ns_path, cache_file))
            else:
                # Clear specific namespace
                ns_path = os.path.join(self._cache_dir, namespace)
                if os.path.exists(ns_path) and os.path.isdir(ns_path):
                    for cache_file in os.listdir(ns_path):
                        os.remove(os.path.join(ns_path, cache_file))
    
    def _get_from_memory(self, namespace: str, key: str) -> Optional[Any]:
        """
        Get a value from the memory cache.
        
        Args:
            namespace: Cache namespace
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        if namespace not in self._memory_cache:
            return None
        
        cache_entry = self._memory_cache[namespace].get(key)
        if cache_entry is None:
            return None
        
        value, expire_time = cache_entry
        
        # Check if expired
        if expire_time is not None and time.time() > expire_time:
            # Remove expired entry
            del self._memory_cache[namespace][key]
            return None
        
        return value
    
    def _set_in_memory(
        self, 
        namespace: str, 
        key: str, 
        value: Any,
        expire: Optional[int] = None
    ) -> None:
        """
        Set a value in the memory cache.
        
        Args:
            namespace: Cache namespace
            key: Cache key
            value: Value to cache
            expire: Expiration time in seconds (optional)
        """
        if namespace not in self._memory_cache:
            self._memory_cache[namespace] = {}
        
        expire_time = None
        if expire is not None:
            expire_time = time.time() + expire
        
        self._memory_cache[namespace][key] = (value, expire_time)
    
    def _delete_from_memory(self, namespace: str, key: str) -> bool:
        """
        Delete a value from the memory cache.
        
        Args:
            namespace: Cache namespace
            key: Cache key
            
        Returns:
            True if the key was deleted, False otherwise
        """
        if namespace not in self._memory_cache:
            return False
        
        if key not in self._memory_cache[namespace]:
            return False
        
        del self._memory_cache[namespace][key]
        return True
    
    async def _get_from_file(self, namespace: str, key: str) -> Optional[Any]:
        """
        Get a value from the file cache.
        
        Args:
            namespace: Cache namespace
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        cache_file = self._get_cache_file_path(namespace, key)
        
        if not os.path.exists(cache_file):
            return None
        
        try:
            loop = asyncio.get_event_loop()
            
            # Read cache file using executor to avoid blocking
            content = await loop.run_in_executor(
                None, 
                functools.partial(self._read_cache_file, cache_file)
            )
            
            if content is None:
                return None
            
            return content
        except Exception as e:
            logger.error(f"Error reading cache file {cache_file}: {e}")
            return None
    
    async def _set_in_file(self, namespace: str, key: str, value: Any) -> None:
        """
        Set a value in the file cache.
        
        Args:
            namespace: Cache namespace
            key: Cache key
            value: Value to cache
        """
        # Create namespace directory if it doesn't exist
        ns_dir = os.path.join(self._cache_dir, namespace)
        os.makedirs(ns_dir, exist_ok=True)
        
        cache_file = self._get_cache_file_path(namespace, key)
        
        try:
            loop = asyncio.get_event_loop()
            
            # Write cache file using executor to avoid blocking
            await loop.run_in_executor(
                None, 
                functools.partial(self._write_cache_file, cache_file, value)
            )
        except Exception as e:
            logger.error(f"Error writing cache file {cache_file}: {e}")
    
    async def _delete_from_file(self, namespace: str, key: str) -> bool:
        """
        Delete a value from the file cache.
        
        Args:
            namespace: Cache namespace
            key: Cache key
            
        Returns:
            True if the key was deleted, False otherwise
        """
        cache_file = self._get_cache_file_path(namespace, key)
        
        if not os.path.exists(cache_file):
            return False
        
        try:
            os.remove(cache_file)
            return True
        except Exception as e:
            logger.error(f"Error deleting cache file {cache_file}: {e}")
            return False
    
    def _get_cache_file_path(self, namespace: str, key: str) -> str:
        """
        Get the file path for a cache key.
        
        Args:
            namespace: Cache namespace
            key: Cache key
            
        Returns:
            File path for the cache key
        """
        # Hash the key to create a safe filename
        key_hash = hashlib.md5(key.encode('utf-8')).hexdigest()
        return os.path.join(self._cache_dir, namespace, f"{key_hash}.cache")
    
    def _read_cache_file(self, cache_file: str) -> Optional[Any]:
        """
        Read and deserialize a cache file.
        
        Args:
            cache_file: Path to the cache file
            
        Returns:
            Deserialized cache content or None if error
        """
        try:
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            logger.error(f"Error deserializing cache file {cache_file}: {e}")
            return None
    
    def _write_cache_file(self, cache_file: str, value: Any) -> None:
        """
        Serialize and write a value to a cache file.
        
        Args:
            cache_file: Path to the cache file
            value: Value to serialize and write
        """
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(value, f)
        except Exception as e:
            logger.error(f"Error serializing value for cache file {cache_file}: {e}")
    
    def _format_key(self, *args, **kwargs) -> str:
        """
        Format function arguments into a cache key.
        
        Returns:
            Formatted cache key string
        """
        # Convert args and kwargs to string representation
        args_str = str(args) if args else ""
        kwargs_str = str(sorted(kwargs.items())) if kwargs else ""
        
        # Combine and hash
        key = f"{args_str}:{kwargs_str}"
        return key


# Create a cache decorator for function results
def cache(
    namespace: str, 
    key_prefix: str = "",
    expire: Optional[int] = None,
    cache_type: CacheType = CacheType.BOTH
):
    """
    Decorator for caching function results.
    
    Args:
        namespace: Cache namespace
        key_prefix: Prefix for cache keys
        expire: Cache expiration time in seconds
        cache_type: Type of cache to use
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache service instance
            cache_service = cache_service_instance
            
            # Format cache key
            if key_prefix:
                arg_key = cache_service._format_key(*args, **kwargs)
                key = f"{key_prefix}:{arg_key}"
            else:
                key = cache_service._format_key(*args, **kwargs)
            
            # Try to get from cache
            cached_result = await cache_service.get(
                namespace, key, default=None, cache_type=cache_type
            )
            
            if cached_result is not None:
                return cached_result
            
            # Call original function
            result = await func(*args, **kwargs)
            
            # Cache the result
            await cache_service.set(
                namespace, key, result, expire=expire, cache_type=cache_type
            )
            
            return result
        
        return wrapper
    
    return decorator


# Create a singleton instance
cache_service_instance = CacheService()

# Convenience functions for direct module use
async def get_cached(namespace: str, key: str, default: Any = None, **kwargs) -> Any:
    """Get a value from the cache."""
    return await cache_service_instance.get(namespace, key, default, **kwargs)

async def set_cached(namespace: str, key: str, value: Any, **kwargs) -> None:
    """Set a value in the cache."""
    await cache_service_instance.set(namespace, key, value, **kwargs)

async def delete_cached(namespace: str, key: str, **kwargs) -> bool:
    """Delete a value from the cache."""
    return await cache_service_instance.delete(namespace, key, **kwargs)

async def clear_cache(namespace: Optional[str] = None, **kwargs) -> None:
    """Clear the cache for a namespace or all namespaces."""
    await cache_service_instance.clear(namespace, **kwargs) 