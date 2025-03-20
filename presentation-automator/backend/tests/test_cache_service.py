"""
Test module for the cache service.
"""

import asyncio
import os
import sys
import time
import pytest

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.services.cache_service import get_cached, set_cached, delete_cached, clear_cache, cache, CacheType


@pytest.mark.asyncio
async def test_cache_service_basic():
    """Test basic cache operations."""
    
    # Set a value in the cache
    await set_cached("test_namespace", "test_key", "test_value")
    
    # Get the value from the cache
    value = await get_cached("test_namespace", "test_key")
    assert value == "test_value"
    
    # Get a non-existent value
    value = await get_cached("test_namespace", "non_existent_key", default="default_value")
    assert value == "default_value"
    
    # Delete the value
    result = await delete_cached("test_namespace", "test_key")
    assert result is True
    
    # Verify it's deleted
    value = await get_cached("test_namespace", "test_key")
    assert value is None
    
    # Clean up
    await clear_cache("test_namespace")


@pytest.mark.asyncio
async def test_cache_decorator():
    """Test the cache decorator."""
    
    call_count = 0
    
    # Define a function with the cache decorator
    @cache(namespace="test_cache", expire=5)
    async def cached_function(arg1, arg2):
        nonlocal call_count
        call_count += 1
        return f"Result: {arg1} + {arg2} = {arg1 + arg2}"
    
    # Call the function multiple times with the same args
    result1 = await cached_function(1, 2)
    result2 = await cached_function(1, 2)  # Should hit cache
    
    # Check that the function was only called once
    assert call_count == 1
    assert result1 == result2
    
    # Call with different args (should miss cache)
    result3 = await cached_function(3, 4)
    assert call_count == 2
    assert result3 != result1
    
    # Clear the cache
    await clear_cache("test_cache")


@pytest.mark.asyncio
async def test_cache_types():
    """Test different cache types."""
    
    # Test memory cache
    await set_cached("test_namespace", "memory_key", "memory_value", cache_type=CacheType.MEMORY)
    value = await get_cached("test_namespace", "memory_key", cache_type=CacheType.MEMORY)
    assert value == "memory_value"
    
    # Memory cache should not be available in file cache
    value = await get_cached("test_namespace", "memory_key", cache_type=CacheType.FILE)
    assert value is None
    
    # Test file cache
    await set_cached("test_namespace", "file_key", "file_value", cache_type=CacheType.FILE)
    value = await get_cached("test_namespace", "file_key", cache_type=CacheType.FILE)
    assert value == "file_value"
    
    # File cache should not be available in memory cache
    value = await get_cached("test_namespace", "file_key", cache_type=CacheType.MEMORY)
    assert value is None
    
    # Test both caches
    await set_cached("test_namespace", "both_key", "both_value", cache_type=CacheType.BOTH)
    
    # Should be available in both caches
    value = await get_cached("test_namespace", "both_key", cache_type=CacheType.MEMORY)
    assert value == "both_value"
    
    value = await get_cached("test_namespace", "both_key", cache_type=CacheType.FILE)
    assert value == "both_value"
    
    # Clean up
    await clear_cache("test_namespace")


if __name__ == "__main__":
    """Run the test directly."""
    asyncio.run(test_cache_service_basic())
    asyncio.run(test_cache_decorator())
    asyncio.run(test_cache_types())
    print("Cache service tests passed!") 