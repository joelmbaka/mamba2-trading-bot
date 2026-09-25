"""
Cache management for the Mamba2 trading bot.
Handles loading and saving of cached data to a JSON file.
"""
import json
from pathlib import Path
from typing import Dict, Any


_FORBIDDEN_CACHE_KEYS = frozenset({"last_account_info"})


class CacheManager:
    """Manages caching of bot data to/from a JSON file."""

    def __init__(self, cache_file: str = "bot_cache.json"):
        """Initialize the cache manager with a cache file path.
        
        Args:
            cache_file: Path to the cache file (default: 'bot_cache.json')
        """
        self.cache_file = Path(cache_file)
        self.cache = self._load_cache()

    @staticmethod
    def _sanitize_cache(cache: Dict[str, Any]) -> Dict[str, Any]:
        """Return cache state with forbidden historical fields removed."""
        return {
            key: value
            for key, value in cache.items()
            if key not in _FORBIDDEN_CACHE_KEYS
        }

    def _write_cache(self, cache: Dict[str, Any]) -> None:
        """Write already-sanitized cache state without logging its contents."""
        with open(self.cache_file, 'w') as f:
            json.dump(cache, f, indent=2)

    def _load_cache(self) -> Dict[str, Any]:
        """Load cache data and immediately scrub forbidden historical state.

        A previously ignored local bot_cache.json may predate the current
        security policy. If a forbidden key is found, the on-disk file is
        rewritten during construction so later saves cannot preserve it.
        """
        if not self.cache_file.exists():
            return {}

        try:
            with open(self.cache_file, 'r') as f:
                loaded = json.load(f)

            if not isinstance(loaded, dict):
                return {}

            sanitized = self._sanitize_cache(loaded)
            if sanitized != loaded:
                self._write_cache(sanitized)
            return sanitized
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Failed to load cache - {e}")
            return {}

    def save_cache(self):
        """Save sanitized cache state to JSON file."""
        try:
            self.cache = self._sanitize_cache(self.cache)
            self._write_cache(self.cache)
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
        """Set a value unless the key is forbidden from persistent cache."""
        if key in _FORBIDDEN_CACHE_KEYS:
            # Defensive cleanup in case callers or tests mutated cache
            # directly before attempting to set the forbidden key.
            self.cache.pop(key, None)
            if save:
                self.save_cache()
            raise ValueError(f"Refusing to cache forbidden key: {key}")

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
