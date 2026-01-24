import os
from pathlib import Path
import subprocess
from typing import List
from urllib.parse import urlparse



def _get_repos_base_dir(repo_url: str) -> Path:
    """
    Extract repository name from a git URL.
    Example:
        https://github.com/user/repo.git -> repo
    """
    path = urlparse(repo_url).path
    name = os.path.basename(path)
    if name.endswith(".git"):
        name = name[:-4]
    return name


def clone_repo(repo_url: str, base_dir: str) -> Path:
    """
    Clone a git repository into base_dir if not already cloned.

    Parameters:
        repo_url (str): GitHub / GitLab repository URL
        base_dir (str): Base directory where repos are stored

    Returns:
        str: Local path to the cloned repository

    Guarantees:
        - Deterministic path
        - No re-cloning if repo already exists
        - Snapshot-based (no pull / update)
    """
    os.makedirs(base_dir, exist_ok=True)

    repo_name = _get_repos_base_dir(repo_url)
    local_repo_path = os.path.join(base_dir, repo_name)

    if os.path.exists(local_repo_path):
        return local_repo_path

    try:
        subprocess.run(
            ["git", "clone", repo_url, local_repo_path],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to clone repository: {repo_url}") from e

    return local_repo_path


# Directories that are never part of the analyzable codebase
IGNORE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".venv",
    "env",
}

# Maximum file size (in bytes) to include (5 MB)
MAX_FILE_SIZE = 5 * 1024 * 1024


def scan_repo_files(repo_path: str) -> list[str]:
    """
    Scan a local repository and return a list of relative file paths
    representing the analyzable codebase.

    Parameters:
        repo_path (str): Path to the local repository root

    Returns:
        list[str]: Sorted list of relative file paths

    Guarantees:
        - Relative paths only
        - Deterministic ordering
        - No symlink traversal
        - No binary detection (handled later)
    """
    file_paths: list[str] = []

    for root, dirs, files in os.walk(repo_path, followlinks=False):
        # Remove ignored directories in-place
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for file_name in files:
            full_path = os.path.join(root, file_name)

            try:
                if os.path.getsize(full_path) > MAX_FILE_SIZE:
                    continue
            except OSError:
                continue

            rel_path = os.path.relpath(full_path, repo_path)
            file_paths.append(rel_path)

    # Deterministic output
    file_paths.sort()
    return file_paths
