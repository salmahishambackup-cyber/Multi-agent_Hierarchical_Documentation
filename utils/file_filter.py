"""File filtering utilities."""

from pathlib import Path
from typing import List, Set


# Supported source file extensions by language
SUPPORTED_EXTENSIONS: Set[str] = {
    '.py',      # Python
    '.java',    # Java
    '.js',      # JavaScript
    '.jsx',     # JavaScript React
    '.ts',      # TypeScript
    '.tsx',     # TypeScript React
    '.c',       # C
    '.h',       # C Header
    '.cpp',     # C++
    '.cc',      # C++
    '.cxx',     # C++
    '.hpp',     # C++ Header
    '.hh',      # C++ Header
    '.cs',      # C#
}


def is_allowed_file(file_path: str) -> bool:
    """
    Check if a file should be analyzed based on extension and path.
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if file should be analyzed, False otherwise
    """
    path = Path(file_path)
    
    # Check extension
    if path.suffix not in SUPPORTED_EXTENSIONS:
        return False
    
    # Additional exclusion patterns
    exclude_patterns = [
        "__pycache__",
        ".git",
        ".venv",
        "venv",
        "env",
        "build",
        "dist",
        ".eggs",
        ".egg-info",
        "node_modules",
        ".gradle",
        "target",
        "out",
        ".pytest_cache",
        ".mypy_cache",
        ".tox",
    ]
    
    # Check if path contains any excluded patterns
    path_str = str(path)
    for pattern in exclude_patterns:
        if pattern in path_str:
            return False
    
    return True


def filter_source_files(files: List[Path]) -> List[Path]:
    """
    Filter a list of files to only include valid source files.
    
    Args:
        files: List of file paths
        
    Returns:
        Filtered list of source files
    """
    return [f for f in files if is_allowed_file(str(f))]
