"""
Phase 2: Docstring Generation

This phase generates Google-style docstrings for modules, functions, and classes
using an LLM-based Writer agent.
"""

from .docstring_generator import DocstringGenerator
from .agents.writer import Writer

__all__ = ["DocstringGenerator", "Writer"]
