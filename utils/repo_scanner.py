"""Repository scanning utilities."""

import subprocess
from pathlib import Path
from typing import List
import tempfile
import shutil


def clone_repo(repo_url: str, target_dir: str = None) -> str:
    """
    Clone a git repository to a temporary or specified directory.
    
    Args:
        repo_url: Git repository URL
        target_dir: Optional target directory
        
    Returns:
        Path to cloned repository
    """
    if target_dir is None:
        target_dir = tempfile.mkdtemp(prefix="repo_")
    
    target_path = Path(target_dir)
    target_path.mkdir(parents=True, exist_ok=True)
    
    subprocess.run(
        ["git", "clone", repo_url, str(target_path)],
        check=True,
        capture_output=True,
        text=True
    )
    
    return str(target_path)


def scan_repo_files(repo_path: str, extensions: List[str] = None) -> List[Path]:
    """
    Scan repository for source files.
    
    Args:
        repo_path: Path to repository
        extensions: List of file extensions to include (e.g., ['.py', '.java'])
                   If None, scans all files
        
    Returns:
        List of file paths
    """
    repo_path = Path(repo_path)
    files = []
    
    # Common patterns to exclude
    exclude_patterns = [
        "__pycache__",
        ".git",
        ".venv",
        "venv",
        "env",
        "build",
        "dist",
        ".eggs",
        "*.egg-info",
        "node_modules",
        ".gradle",
        "target",
        "out",
    ]
    
    if extensions:
        for ext in extensions:
            for file_path in repo_path.rglob(f"*{ext}"):
                should_exclude = any(
                    pattern in str(file_path) for pattern in exclude_patterns
                )
                if not should_exclude:
                    files.append(file_path)
    else:
        for file_path in repo_path.rglob("*"):
            if file_path.is_file():
                should_exclude = any(
                    pattern in str(file_path) for pattern in exclude_patterns
                )
                if not should_exclude:
                    files.append(file_path)
    
    return sorted(files)
