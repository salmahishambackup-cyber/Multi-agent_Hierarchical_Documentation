"""
Content-based caching for LLM results.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Optional


def get_cache_key(content: str) -> str:
    """
    Generate a short cache key from content hash.
    
    Args:
        content: Content to hash
        
    Returns:
        16-character hex digest
    """
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def load_from_cache(cache_dir: Path | str, key: str, category: str = "default") -> Optional[Any]:
    """
    Load cached result if it exists.
    
    Args:
        cache_dir: Root cache directory
        key: Cache key (from get_cache_key)
        category: Cache category (e.g., "docstrings", "readme_sections")
        
    Returns:
        Cached data or None if not found
    """
    cache_path = Path(cache_dir) / category / f"{key}.json"
    if cache_path.exists():
        try:
            return json.loads(cache_path.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def save_to_cache(cache_dir: Path | str, key: str, data: Any, category: str = "default") -> None:
    """
    Save result to cache.
    
    Args:
        cache_dir: Root cache directory
        key: Cache key (from get_cache_key)
        data: Data to cache
        category: Cache category (e.g., "docstrings", "readme_sections")
    """
    cache_path = Path(cache_dir) / category / f"{key}.json"
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
