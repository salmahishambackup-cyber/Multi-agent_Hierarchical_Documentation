"""
Utility functions for artifact inspection and enrichment.
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Name resolution
# ---------------------------------------------------------------------------

def resolve_name_from_ast(
    entry: Dict[str, Any],
    ast_data: Dict[str, Any],
) -> str:
    """
    Cross-reference ast.json to resolve an unknown function/method name.

    Strategy:
    1. Match by file name and byte offset range.
    2. Extract bare name from a ``symbol`` string by stripping parameter
       signatures.
    3. Fall back to function order within the file if offset is ambiguous.
    4. Return ``"UNRESOLVED — manual inspection required"`` if none of the
       above succeed.

    Args:
        entry: A single entry from doc_artifacts.json that may have
               ``name == "unknown"`` or missing name.
        ast_data: Parsed contents of ast.json keyed by file path.

    Returns:
        Resolved name string, or the sentinel ``"UNRESOLVED — manual
        inspection required"``.
    """
    # Try stripping parameters from a "symbol" field first
    symbol = entry.get("symbol", "") or ""
    if symbol:
        bare = re.split(r"[\(\[]", symbol)[0].strip()
        if bare:
            return bare

    entry_file = entry.get("file", "") or ""
    _bs = entry.get("byte_start")
    start_offset = _bs if _bs is not None else entry.get("start_byte")
    _be = entry.get("byte_end")
    end_offset = _be if _be is not None else entry.get("end_byte")

    for ast_file_key, ast_file_data in ast_data.items():
        # Loose file-name matching
        if not _files_match(entry_file, ast_file_key):
            continue

        functions = ast_file_data.get("functions", []) or []
        classes = ast_file_data.get("classes", []) or []

        all_symbols = functions + classes

        if start_offset is not None and end_offset is not None:
            # Match by offset range
            for sym in all_symbols:
                _ss = sym.get("byte_start")
                sym_start = _ss if _ss is not None else sym.get("start_byte")
                _se = sym.get("byte_end")
                sym_end = _se if _se is not None else sym.get("end_byte")
                if sym_start is not None and sym_end is not None:
                    if sym_start <= start_offset and end_offset <= sym_end:
                        name = sym.get("name", "")
                        if name:
                            return name

        # Fall back to order within file using "index" field
        index = entry.get("index")
        if index is not None and index < len(all_symbols):
            name = all_symbols[index].get("name", "")
            if name:
                return name

    return "UNRESOLVED — manual inspection required"


def _files_match(entry_file: str, ast_key: str) -> bool:
    """Return True when *entry_file* and *ast_key* refer to the same file."""
    if not entry_file or not ast_key:
        return False
    # Normalise separators and compare basename and parent
    ef = Path(entry_file.replace("\\", "/"))
    ak = Path(ast_key.replace("\\", "/"))
    # Exact match or basename match
    return ef == ak or ef.name == ak.name or ef.stem == ak.stem


# ---------------------------------------------------------------------------
# Duplicate docstring detection
# ---------------------------------------------------------------------------

def detect_duplicate_docstrings(
    doc_entries: List[Dict[str, Any]],
) -> List[Tuple[int, int, str]]:
    """
    Find copy-pasted docstrings across multiple entries.

    Args:
        doc_entries: List of documentation entries (from doc_artifacts.json).

    Returns:
        List of ``(index_a, index_b, docstring)`` tuples for every pair
        that shares an identical docstring.
    """
    seen: Dict[str, List[int]] = defaultdict(list)

    for idx, entry in enumerate(doc_entries):
        docstring = (
            entry.get("docstring")
            or entry.get("detailed_description")
            or entry.get("short_description")
            or ""
        )
        normalized = docstring.strip()
        if normalized:
            seen[normalized].append(idx)

    duplicates: List[Tuple[int, int, str]] = []
    for docstring, indices in seen.items():
        if len(indices) > 1:
            for i in range(len(indices)):
                for j in range(i + 1, len(indices)):
                    duplicates.append((indices[i], indices[j], docstring))

    return duplicates


# ---------------------------------------------------------------------------
# Business context inference
# ---------------------------------------------------------------------------

_PIPELINE_STAGE_SIGNALS: Dict[str, List[str]] = {
    "ingestion": ["load", "read", "fetch", "import", "ingest", "scan"],
    "analysis": ["analyze", "analyse", "parse", "extract", "inspect", "detect"],
    "generation": ["generate", "create", "produce", "build", "write", "render"],
    "validation": ["validate", "check", "verify", "assert", "lint", "review"],
    "evaluation": ["evaluate", "score", "rate", "measure", "benchmark"],
    "output": ["save", "export", "dump", "output", "persist", "store"],
    "orchestration": ["run", "execute", "orchestrate", "coordinate", "dispatch"],
    "utility": ["ensure", "format", "convert", "normalize", "clean", "helper"],
}


def extract_business_context(entry: Dict[str, Any]) -> str:
    """
    Infer a short business context from available code signals.

    Uses the entry's name, signature, and any existing description to
    produce a concise statement about *why* this symbol exists.

    Args:
        entry: A documentation entry dictionary.

    Returns:
        A one-to-two sentence business context string.
    """
    name = entry.get("name", "") or ""
    description = (
        entry.get("short_description")
        or entry.get("detailed_description")
        or entry.get("docstring")
        or ""
    )
    file_path = entry.get("file", "") or ""

    # Derive stage from naming patterns
    stage = _infer_pipeline_stage(name, file_path)

    if description:
        return f"Part of the {stage} stage. {description.rstrip('.')}."
    if name:
        readable = re.sub(r"([a-z])([A-Z])", r"\1 \2", name).replace("_", " ").lower()
        return f"Part of the {stage} stage. Responsible for {readable}."
    return f"Part of the {stage} stage."


def _infer_pipeline_stage(name: str, file_path: str) -> str:
    """Heuristically determine pipeline stage from symbol/file name."""
    haystack = (name + " " + file_path).lower()
    for stage, signals in _PIPELINE_STAGE_SIGNALS.items():
        if any(s in haystack for s in signals):
            return stage
    return "processing"


# ---------------------------------------------------------------------------
# Mermaid flowchart generation
# ---------------------------------------------------------------------------

def generate_mermaid_flowchart(pipeline_stages: Optional[List[str]] = None) -> str:
    """
    Create a Mermaid flowchart that represents the documentation pipeline.

    Args:
        pipeline_stages: Optional ordered list of stage names. Defaults to
                         the standard eight-phase pipeline when omitted.

    Returns:
        A string containing a complete Mermaid ``flowchart TD`` block.
    """
    if pipeline_stages is None:
        pipeline_stages = [
            "Phase 1: Static Analysis",
            "Phase 2: Docstring Generation",
            "Phase 3: README Generation",
            "Phase 4: Validation",
            "Phase 5: Evaluation",
            "Phase 6: Artifact Diagnosis",
            "Phase 7: Artifact Enrichment",
            "Phase 8: Enhanced README",
        ]

    lines = ["```mermaid", "flowchart TD"]
    prev_id: Optional[str] = None

    for i, stage in enumerate(pipeline_stages):
        node_id = f"P{i + 1}"
        safe_label = stage.replace('"', "'")
        lines.append(f'    {node_id}["{safe_label}"]')
        if prev_id is not None:
            lines.append(f"    {prev_id} --> {node_id}")
        prev_id = node_id

    lines.append("```")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Enriched artifact validation
# ---------------------------------------------------------------------------

_REQUIRED_DOC_FIELDS = {
    "name",
    "file",
    "type",
    "short_description",
    "detailed_description",
    "business_context",
    "pipeline_stage",
}


def validate_enriched_artifacts(
    doc_entries: List[Dict[str, Any]],
) -> List[str]:
    """
    Ensure all required fields are present in every enriched doc entry.

    Args:
        doc_entries: List of enriched documentation entry dictionaries.

    Returns:
        List of human-readable validation error strings (empty means valid).
    """
    errors: List[str] = []

    for idx, entry in enumerate(doc_entries):
        entry_id = entry.get("name") or f"entry[{idx}]"
        for field in _REQUIRED_DOC_FIELDS:
            value = entry.get(field)
            if not value:
                errors.append(f"Entry '{entry_id}': missing or empty field '{field}'")

        # Name must never be "unknown"
        name = entry.get("name", "")
        if name.lower() in {"unknown", "none", ""}:
            errors.append(
                f"Entry [{idx}]: name is '{name}' — must be resolved before export"
            )

    return errors
