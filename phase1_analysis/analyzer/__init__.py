"""
Analyzer module for static code analysis using tree-sitter.
Provides fast, LLM-free project analysis.
"""

from .ast_extractor import extract_ast_info, normalize_file_path
from .dependency_builder import build_dependency_graph
from .component_extractor import extract_components
from .language_router import detect_language
from .tree_sitter_loader import get_parser
from .file_metrics import compute_file_metrics

__all__ = [
    "extract_ast_info",
    "normalize_file_path",
    "build_dependency_graph",
    "extract_components",
    "detect_language",
    "get_parser",
    "compute_file_metrics",
]
