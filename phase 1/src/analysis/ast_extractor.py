# analysis/ast_extractor.py

from pathlib import Path
from analysis.language_router import detect_language
from analysis.tree_sitter_loader import get_parser
from analysis.ast_utils import walk_tree


def normalize_file_path(file_path: str, repo_root: str) -> str:
    """
    Convert file paths to repo-relative POSIX format.
    
    Args:
        file_path: Either absolute or relative file path
        repo_root: Root directory of the repository
    
    Returns:
        Repo-relative POSIX path (e.g., 'api/config.py')
    """
    file_path = Path(file_path).resolve()
    repo_root = Path(repo_root).resolve()
    
    try:
        rel = file_path.relative_to(repo_root)
    except ValueError:
        # If file is not under repo_root, return as-is but convert to POSIX
        return file_path.as_posix()
    
    return rel.as_posix()


def extract_ast_info(file_path: str, content: bytes, repo_root: str = None) -> dict | None:
    """
    Extract AST information from a source file.
    
    Args:
        file_path: Path to the file (absolute or relative)
        content: Raw file content as bytes
        repo_root: Root directory of the repository (for path normalization)
    
    Returns:
        Dictionary with AST summary or None if language not supported
    """
    language = detect_language(file_path)
    if not language:
        return None

    parser = get_parser(language)
    tree = parser.parse(content)

    # Normalize file path if repo_root is provided
    normalized_file_path = file_path
    if repo_root:
        normalized_file_path = normalize_file_path(file_path, repo_root)

    results = {
        "file": normalized_file_path,
        "language": language,
        "imports": [],
        "functions": [],
        "classes": []
    }

    # Start traversal from first real level
    root = tree.root_node
    for child in root.children:
        walk_tree(
            node=child,
            source=content,
            results=results,
            lang=language,
            file_path=normalized_file_path,
            depth=1
        )

    return results