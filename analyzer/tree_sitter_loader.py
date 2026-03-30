# analysis/tree_sitter_loader.py

_PARSER_CACHE = {}

# Sentinel indicating tree-sitter is unavailable for a language
_UNAVAILABLE = object()


def _try_tree_sitter_languages(language: str):
    """Try loading parser via tree_sitter_languages (tree-sitter <0.21)."""
    from tree_sitter_languages import get_parser as _get_parser
    return _get_parser(language)


def _try_individual_package(language: str):
    """Try loading parser via individual tree-sitter-{lang} packages (tree-sitter >=0.22)."""
    import importlib
    from tree_sitter import Language, Parser

    lang_module_map = {
        "python": "tree_sitter_python",
        "java": "tree_sitter_java",
        "javascript": "tree_sitter_javascript",
        "typescript": "tree_sitter_typescript",
        "c": "tree_sitter_c",
        "cpp": "tree_sitter_cpp",
        "csharp": "tree_sitter_c_sharp",
    }

    module_name = lang_module_map.get(language)
    if not module_name:
        raise ImportError(f"No individual tree-sitter package mapping for '{language}'")

    mod = importlib.import_module(module_name)
    lang_fn = getattr(mod, "language", None)
    if lang_fn is None:
        raise ImportError(f"Module {module_name} has no language() function")

    ts_language = Language(lang_fn())
    parser = Parser(ts_language)
    return parser


def get_parser(language: str):
    """
    Returns a cached tree-sitter Parser for the given language.

    Tries multiple strategies:
    1. tree_sitter_languages package (works with tree-sitter <0.21)
    2. Individual tree-sitter-{lang} packages (works with tree-sitter >=0.22)

    Returns None if no tree-sitter parser is available.
    """
    if language in _PARSER_CACHE:
        cached = _PARSER_CACHE[language]
        return None if cached is _UNAVAILABLE else cached

    strategies = [_try_tree_sitter_languages, _try_individual_package]

    for strategy in strategies:
        try:
            parser = strategy(language)
            _PARSER_CACHE[language] = parser
            return parser
        except (TypeError, ImportError, OSError, Exception):
            continue

    _PARSER_CACHE[language] = _UNAVAILABLE
    return None
