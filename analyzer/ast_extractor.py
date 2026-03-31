# analysis/ast_extractor.py

import ast as stdlib_ast
from pathlib import Path
from analyzer.language_router import detect_language
from analyzer.tree_sitter_loader import get_parser
from analyzer.ast_utils import walk_tree


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


# ---------------------------------------------------------------------------
# Python stdlib ast fallback
# ---------------------------------------------------------------------------

def _get_function_signature(node: stdlib_ast.FunctionDef, source_lines: list[str]) -> str:
    """Build a function signature string from a stdlib AST FunctionDef node."""
    name = node.name
    args = node.args

    parts = []
    num_args = len(args.args)
    num_defaults = len(args.defaults)
    first_default_idx = num_args - num_defaults

    for i, arg in enumerate(args.args):
        part = arg.arg
        annotation = arg.annotation
        if annotation:
            part += f": {stdlib_ast.unparse(annotation)}"
        if i >= first_default_idx:
            default = args.defaults[i - first_default_idx]
            part += f"={stdlib_ast.unparse(default)}"
        parts.append(part)

    if args.vararg:
        va = f"*{args.vararg.arg}"
        if args.vararg.annotation:
            va += f": {stdlib_ast.unparse(args.vararg.annotation)}"
        parts.append(va)

    for i, arg in enumerate(args.kwonlyargs):
        part = arg.arg
        if arg.annotation:
            part += f": {stdlib_ast.unparse(arg.annotation)}"
        if i < len(args.kw_defaults) and args.kw_defaults[i] is not None:
            part += f"={stdlib_ast.unparse(args.kw_defaults[i])}"
        parts.append(part)

    if args.kwarg:
        kw = f"**{args.kwarg.arg}"
        if args.kwarg.annotation:
            kw += f": {stdlib_ast.unparse(args.kwarg.annotation)}"
        parts.append(kw)

    return f"{name}({', '.join(parts)})"


def _get_docstring(node) -> str | None:
    """Extract docstring from an AST node (class or function)."""
    return stdlib_ast.get_docstring(node)


def _get_decorators(node) -> list[str]:
    """Extract decorator names from a function or class node."""
    decorators = []
    for dec in getattr(node, "decorator_list", []):
        try:
            decorators.append(stdlib_ast.unparse(dec))
        except Exception:
            pass
    return decorators


def _get_base_classes(node: stdlib_ast.ClassDef) -> list[str]:
    """Extract base class names from a ClassDef node."""
    bases = []
    for base in node.bases:
        try:
            bases.append(stdlib_ast.unparse(base))
        except Exception:
            pass
    return bases


def _extract_python_ast_fallback(content: bytes, normalized_file_path: str) -> dict | None:
    """
    Fallback AST extraction for Python files using the stdlib ast module.

    Produces the same output structure as the tree-sitter path, enriched with
    docstrings, decorators, base classes, and return type annotations.
    """
    try:
        source_text = content.decode("utf-8", errors="ignore")
    except Exception:
        return None

    try:
        tree = stdlib_ast.parse(source_text, filename=normalized_file_path)
    except SyntaxError:
        return None

    source_lines = source_text.splitlines()
    source_bytes = content

    results: dict = {
        "file": normalized_file_path,
        "language": "python",
        "imports": [],
        "functions": [],
        "classes": [],
    }

    def _byte_offset(lineno: int, col_offset: int) -> int:
        """Approximate byte offset from line/col."""
        offset = col_offset
        for i, line in enumerate(source_lines):
            if i + 1 >= lineno:
                break
            offset += len(line) + 1  # +1 for newline
        return offset

    def _end_byte_offset(node) -> int:
        end_line = getattr(node, "end_lineno", None) or node.lineno
        end_col = getattr(node, "end_col_offset", None) or 0
        return _byte_offset(end_line, end_col)

    def _make_node_id(node) -> str:
        start = _byte_offset(node.lineno, node.col_offset)
        end = _end_byte_offset(node)
        return f"ast:{normalized_file_path}:{start}:{end}"

    for top_node in stdlib_ast.iter_child_nodes(tree):
        # --- Imports ---
        if isinstance(top_node, stdlib_ast.Import):
            for alias in top_node.names:
                symbol = f"import {alias.name}"
                results["imports"].append({
                    "node_id": _make_node_id(top_node),
                    "kind": "import",
                    "symbol": symbol,
                    "language": "python",
                    "location": {
                        "start_byte": _byte_offset(top_node.lineno, top_node.col_offset),
                        "end_byte": _end_byte_offset(top_node),
                    },
                })

        elif isinstance(top_node, stdlib_ast.ImportFrom):
            module = top_node.module or ""
            names = ", ".join(a.name for a in top_node.names)
            symbol = f"from {module} import {names}"
            results["imports"].append({
                "node_id": _make_node_id(top_node),
                "kind": "import",
                "symbol": symbol,
                "language": "python",
                "location": {
                    "start_byte": _byte_offset(top_node.lineno, top_node.col_offset),
                    "end_byte": _end_byte_offset(top_node),
                },
            })

        # --- Top-level functions ---
        elif isinstance(top_node, stdlib_ast.FunctionDef) or isinstance(top_node, stdlib_ast.AsyncFunctionDef):
            sig = _get_function_signature(top_node, source_lines)
            entry = {
                "node_id": _make_node_id(top_node),
                "kind": "function_definition",
                "symbol": sig,
                "language": "python",
                "location": {
                    "start_byte": _byte_offset(top_node.lineno, top_node.col_offset),
                    "end_byte": _end_byte_offset(top_node),
                },
            }
            docstring = _get_docstring(top_node)
            if docstring:
                entry["docstring"] = docstring
            decorators = _get_decorators(top_node)
            if decorators:
                entry["decorators"] = decorators
            if top_node.returns:
                try:
                    entry["return_type"] = stdlib_ast.unparse(top_node.returns)
                except Exception:
                    pass
            results["functions"].append(entry)

        # --- Classes ---
        elif isinstance(top_node, stdlib_ast.ClassDef):
            class_entry = {
                "node_id": _make_node_id(top_node),
                "kind": "class_definition",
                "symbol": top_node.name,
                "language": "python",
                "location": {
                    "start_byte": _byte_offset(top_node.lineno, top_node.col_offset),
                    "end_byte": _end_byte_offset(top_node),
                },
            }
            docstring = _get_docstring(top_node)
            if docstring:
                class_entry["docstring"] = docstring
            decorators = _get_decorators(top_node)
            if decorators:
                class_entry["decorators"] = decorators
            bases = _get_base_classes(top_node)
            if bases:
                class_entry["bases"] = bases
            results["classes"].append(class_entry)

            # Extract methods inside the class (depth 2)
            for class_child in stdlib_ast.iter_child_nodes(top_node):
                if isinstance(class_child, (stdlib_ast.FunctionDef, stdlib_ast.AsyncFunctionDef)):
                    sig = _get_function_signature(class_child, source_lines)
                    method_entry = {
                        "node_id": _make_node_id(class_child),
                        "kind": "function_definition",
                        "symbol": sig,
                        "language": "python",
                        "location": {
                            "start_byte": _byte_offset(class_child.lineno, class_child.col_offset),
                            "end_byte": _end_byte_offset(class_child),
                        },
                    }
                    method_doc = _get_docstring(class_child)
                    if method_doc:
                        method_entry["docstring"] = method_doc
                    method_decorators = _get_decorators(class_child)
                    if method_decorators:
                        method_entry["decorators"] = method_decorators
                    if class_child.returns:
                        try:
                            method_entry["return_type"] = stdlib_ast.unparse(class_child.returns)
                        except Exception:
                            pass
                    results["functions"].append(method_entry)

    return results


# ---------------------------------------------------------------------------
# Main extraction entry point
# ---------------------------------------------------------------------------

def extract_ast_info(file_path: str, content: bytes, repo_root: str = None) -> dict | None:
    """
    Extract AST information from a source file.

    Uses tree-sitter when available, falling back to Python's stdlib ast module
    for Python files when tree-sitter is unavailable or fails.
    
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

    # Normalize file path if repo_root is provided
    normalized_file_path = file_path
    if repo_root:
        normalized_file_path = normalize_file_path(file_path, repo_root)

    # Try tree-sitter first
    try:
        parser = get_parser(language)
    except Exception:
        # get_parser() may raise (e.g. tree-sitter version mismatch)
        parser = None

    if parser is not None:
        try:
            tree = parser.parse(content)

            results = {
                "file": normalized_file_path,
                "language": language,
                "imports": [],
                "functions": [],
                "classes": []
            }

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
        except Exception:
            # Tree-sitter parsing failed; try fallback below
            pass

    # Fallback: use stdlib ast for Python files
    if language == "python":
        return _extract_python_ast_fallback(content, normalized_file_path)

    return None