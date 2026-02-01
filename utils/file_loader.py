"""File loading utilities."""

from pathlib import Path
from typing import Optional


def load_file_bytes(file_path: str) -> Optional[bytes]:
    """
    Load file content as bytes.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File content as bytes, or None if loading fails
    """
    try:
        path = Path(file_path)
        return path.read_bytes()
    except Exception as e:
        print(f"Warning: Failed to read {file_path}: {e}")
        return None


def load_file_text(file_path: str, encoding: str = 'utf-8') -> Optional[str]:
    """
    Load file content as text.
    
    Args:
        file_path: Path to the file
        encoding: Text encoding (default: utf-8)
        
    Returns:
        File content as string, or None if loading fails
    """
    try:
        path = Path(file_path)
        return path.read_text(encoding=encoding)
    except Exception as e:
        print(f"Warning: Failed to read {file_path}: {e}")
        return None
