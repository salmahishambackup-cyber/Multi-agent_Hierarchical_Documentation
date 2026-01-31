"""Path normalization utilities."""

from pathlib import Path
from typing import Union


def normalize_path(file_path: Union[str, Path], repo_root: Union[str, Path]) -> str:
    """
    Convert file path to repo-relative POSIX format.
    
    Args:
        file_path: File path (absolute or relative)
        repo_root: Repository root directory
        
    Returns:
        Repo-relative POSIX path
    """
    file_path = Path(file_path).resolve()
    repo_root = Path(repo_root).resolve()
    
    try:
        rel = file_path.relative_to(repo_root)
        return rel.as_posix()
    except ValueError:
        # If file is not under repo_root, return as-is but convert to POSIX
        return file_path.as_posix()


def to_posix(path: Union[str, Path]) -> str:
    """
    Convert path to POSIX format.
    
    Args:
        path: Path to convert
        
    Returns:
        POSIX-formatted path string
    """
    return Path(path).as_posix()


def ensure_absolute(path: Union[str, Path]) -> Path:
    """
    Ensure path is absolute.
    
    Args:
        path: Path to process
        
    Returns:
        Absolute path
    """
    return Path(path).resolve()
