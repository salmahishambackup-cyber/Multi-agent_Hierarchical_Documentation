"""
Profiling utilities for timing and memory tracking.
"""

from __future__ import annotations

import time
import psutil
import functools
from typing import Callable, Any


def format_memory(bytes_val: int) -> str:
    """
    Format memory in human-readable units.
    
    Args:
        bytes_val: Memory in bytes
        
    Returns:
        Formatted string (e.g., "3.8GB", "512MB")
    """
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes_val < 1024.0:
            return f"{bytes_val:.1f}{unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.1f}TB"


def profile_phase(phase_name: str) -> Callable:
    """
    Decorator to profile execution time and memory usage of a phase.
    
    Args:
        phase_name: Name of the phase (e.g., "Phase 1: Analysis")
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Get initial memory
            process = psutil.Process()
            mem_before = process.memory_info().rss
            
            # Time execution
            start = time.time()
            result = func(*args, **kwargs)
            elapsed = time.time() - start
            
            # Get final memory
            mem_after = process.memory_info().rss
            mem_delta = mem_after - mem_before
            
            # Print stats
            print(f"[{phase_name}] Time: {elapsed:.1f}s | Memory: {format_memory(mem_after)}")
            
            return result
        return wrapper
    return decorator
