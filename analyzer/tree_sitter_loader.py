# analysis/tree_sitter_loader.py

from tree_sitter_languages import get_parser as _get_parser

_PARSER_CACHE = {}


def get_parser(language: str):
    """
    Returns a cached tree-sitter Parser for the given language.
    Uses tree_sitter_languages to avoid manual grammar builds.
    """
    if language not in _PARSER_CACHE:
        _PARSER_CACHE[language] = _get_parser(language)

    return _PARSER_CACHE[language]
