import os

LANGUAGE_EXTENSIONS = {
    "python": [".py"],
    "java": [".java"],
    "javascript": [".js"],
    "typescript": [".ts", ".tsx"],
    "c": [".c",".h"],
    "cpp": [".cpp", ".cc", ".cxx", ".hpp", ".h"],
    "csharp": [".cs"]
}


def detect_language(file_path: str) -> str | None:
    _, ext = os.path.splitext(file_path.lower())
    for lang, exts in LANGUAGE_EXTENSIONS.items():
        if ext in exts:
            return lang
    return None
