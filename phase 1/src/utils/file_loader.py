import os


# Files larger than this will be skipped (5 MB)
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024


def load_file_bytes(file_path: str) -> bytes:
    """
    Load a file as raw bytes in a safe, research-friendly way.

    - Skips very large files
    - Skips directories
    - Raises exceptions for unreadable or binary-heavy files

    Returns:
        bytes: raw file content

    Raises:
        ValueError: if file should not be processed
        IOError: if file cannot be read
    """

    if not os.path.isfile(file_path):
        raise ValueError(f"Not a regular file: {file_path}")

    file_size = os.path.getsize(file_path)
    if file_size > MAX_FILE_SIZE_BYTES:
        raise ValueError(f"File too large: {file_path}")

    with open(file_path, "rb") as f:
        content = f.read()

    # Heuristic: skip binary-heavy files
    if b"\x00" in content:
        raise ValueError(f"Binary file detected: {file_path}")

    return content
