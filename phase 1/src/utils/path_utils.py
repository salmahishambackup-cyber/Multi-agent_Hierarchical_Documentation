import os

def normalize_path(path: str) -> str:
    """
    Normalize path to use forward slashes and no trailing separators.
    """
    return os.path.normpath(path).replace("\\", "/")