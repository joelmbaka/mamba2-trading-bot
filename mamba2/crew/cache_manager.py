"""
Cache management for the Mamba2 trading bot.
Handles loading and saving of cached data to a JSON file.
"""
import json
from pathlib import Path
from typing import Dict, Any


class CacheManager:
    """Manages caching of bot data to/from a JSON file."""

    def __init__(self, cache_file: str = "bot_cache.json"):
        """Initialize the cache manager with a cache file path.
        
        Args:
            cache_file: Path to the cache file (default: 'bot_cache.json')
        """
        self.cache_file = Path(cache_file)
        self.cache = self._load_cache()

    def _load_cache(self) -> Dict[str, Any]:
        """Load cached data from JSON file.
        
        Returns:
            Dict containing the cached data, or empty dict if no cache exists
        """
        if not self.cache_file.exists():
            return {}
        
        try:
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Failed to load cache - {e}")
            return {}

    def save_cache(self):
        """Save current cache to JSON file."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except IOError as e:
            print(f"Warning: Failed to save cache - {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the cache.
        
        Args:
            key: The key to look up in the cache
            default: Default value to return if key is not found
            
        Returns:
            The cached value or default if key not found
        """
        return self.cache.get(key, default)
    
    def set(self, key: str, value: Any, save: bool = False):
        """Set a value in the cache.
        
        Args:
            key: The key to set in the cache
            value: The value to store
            save: If True, save the cache to disk immediately
        """
        self.cache[key] = value
        if save:
            self.save_cache()
    
    def clear(self, save: bool = False):
        """Clear all cached data.
        
        Args:
            save: If True, save the empty cache to disk immediately
        """
        self.cache = {}
        if save:
            self.save_cache()
