"""Deterministic ID generation utilities."""

import hashlib
from typing import List, Union


def generate_id(components: List[Union[str, int]], prefix: str = "") -> str:
    """
    Generate a deterministic ID from components.
    
    Args:
        components: List of components to hash
        prefix: Optional prefix for the ID
        
    Returns:
        Deterministic ID string
    """
    # Join components into a single string
    combined = "|".join(str(c) for c in components)
    
    # Generate hash
    hash_obj = hashlib.sha256(combined.encode('utf-8'))
    hash_str = hash_obj.hexdigest()[:16]  # Use first 16 chars
    
    if prefix:
        return f"{prefix}_{hash_str}"
    return hash_str


def generate_file_id(file_path: str, repo_root: str = "") -> str:
    """
    Generate a deterministic ID for a file.
    
    Args:
        file_path: Path to the file
        repo_root: Optional repository root for relative paths
        
    Returns:
        File ID
    """
    if repo_root:
        from pathlib import Path
        try:
            file_path = Path(file_path).relative_to(repo_root).as_posix()
        except ValueError:
            pass
    
    return generate_id([file_path], prefix="file")


def generate_function_id(file_path: str, function_name: str) -> str:
    """
    Generate a deterministic ID for a function.
    
    Args:
        file_path: Path to the file containing the function
        function_name: Name of the function
        
    Returns:
        Function ID
    """
    return generate_id([file_path, function_name], prefix="func")


def generate_class_id(file_path: str, class_name: str) -> str:
    """
    Generate a deterministic ID for a class.
    
    Args:
        file_path: Path to the file containing the class
        class_name: Name of the class
        
    Returns:
        Class ID
    """
    return generate_id([file_path, class_name], prefix="class")
