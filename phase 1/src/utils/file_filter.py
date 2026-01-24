ALLOWED_EXTENSIONS = {
    ".py", ".js", ".ts", ".java", ".c", ".cpp", ".h",
    ".go", ".rs", ".md", ".txt", ".yaml", ".yml", ".json"
}

def is_allowed_file(path: str) -> bool:
    """
    Decide whether a file should be included in analysis.
    """
    for ext in ALLOWED_EXTENSIONS:
        if path.lower().endswith(ext):
            return True
    return False
