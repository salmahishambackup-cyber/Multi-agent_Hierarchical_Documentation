"""
Phase 1: Static Code Analysis

This phase performs static analysis on the repository using tree-sitter.
It extracts AST information, builds dependency graphs, and identifies components.
"""

from .phase1_analyzer import Analyzer
from .agents.structural_agent import StructuralAgent

__all__ = ["Analyzer", "StructuralAgent"]
