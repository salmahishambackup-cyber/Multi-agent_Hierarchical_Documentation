"""
Artifact Critic agent — inspects artifact JSON files and produces structured
weakness reports.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from agents.base_agent import BaseAgent
from schemas.enriched_artifacts import Severity, Weakness, WeaknessReport


# ---------------------------------------------------------------------------
# Known artifacts and their canonical file names
# ---------------------------------------------------------------------------

_ARTIFACT_FILES = {
    "doc_artifacts": "doc_artifacts.json",
    "ast": "ast.json",
    "dependencies": "dependencies_normalized.json",
    "components": "components.json",
    "edge_cases": "edge_cases.json",
}


class ArtifactCritic(BaseAgent):
    """
    Inspects artifact JSON files in *artifacts_dir* and returns a
    :class:`~schemas.enriched_artifacts.WeaknessReport` that categorises
    every detected issue by severity.

    Severity definitions
    --------------------
    CRITICAL
        Issues that make the artifact unusable or actively misleading.
    MAJOR
        Missing fields that are required for complete documentation.
    MINOR
        Optional fields whose absence reduces quality.
    """

    def __init__(self, repo_path: str, artifacts_dir: str = "./artifacts"):
        super().__init__(repo_path=repo_path, artifacts_dir=artifacts_dir)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> Dict[str, Any]:
        """
        Inspect all known artifact files and return a serialisable dict.

        Returns:
            Dictionary containing the weakness report and summary counts.
        """
        report = self.audit()
        report_dict = report.model_dump()
        # Persist report for downstream agents
        self.save_artifact("weakness_report.json", report_dict)
        print(f"📋 Artifact Critic: {report.summary()}")
        return report_dict

    def audit(self) -> WeaknessReport:
        """
        Audit all artifact files and return a :class:`WeaknessReport`.

        Returns:
            Structured weakness report with all detected issues.
        """
        weaknesses: List[Weakness] = []

        for key, filename in _ARTIFACT_FILES.items():
            artifact_path = self.artifacts_dir / filename
            if not artifact_path.exists():
                weaknesses.append(
                    Weakness(
                        artifact=filename,
                        severity=Severity.MAJOR,
                        message=f"Artifact file '{filename}' not found in {self.artifacts_dir}",
                    )
                )
                continue

            data = self._load_json(artifact_path)
            if data is None:
                weaknesses.append(
                    Weakness(
                        artifact=filename,
                        severity=Severity.CRITICAL,
                        message=f"Artifact file '{filename}' could not be parsed as JSON",
                    )
                )
                continue

            checker = getattr(self, f"_check_{key}", None)
            if checker is not None:
                weaknesses.extend(checker(data))

        return WeaknessReport(
            artifact_dir=str(self.artifacts_dir),
            weaknesses=weaknesses,
        )

    # ------------------------------------------------------------------
    # Per-artifact checkers
    # ------------------------------------------------------------------

    def _check_doc_artifacts(self, data: Any) -> List[Weakness]:
        weaknesses: List[Weakness] = []
        entries: List[Dict[str, Any]] = []

        if isinstance(data, list):
            entries = data
        elif isinstance(data, dict):
            # Support {symbols: [...]} or {entries: [...]} envelopes
            entries = (
                data.get("symbols")
                or data.get("entries")
                or data.get("functions")
                or []
            )
            if not isinstance(entries, list):
                entries = []

        # Collect docstrings to detect duplicates
        docstring_map: Dict[str, List[str]] = {}

        for idx, entry in enumerate(entries):
            entry_id = entry.get("name") or f"[{idx}]"

            # CRITICAL: unknown / missing name
            name = entry.get("name")
            if not name or str(name).lower() in {"unknown", "none", "null"}:
                weaknesses.append(
                    Weakness(
                        artifact="doc_artifacts.json",
                        entry_id=entry_id,
                        field="name",
                        severity=Severity.CRITICAL,
                        message=f"Entry [{idx}] has unresolvable name: '{name}'",
                    )
                )

            # CRITICAL: raw source code inside docstring
            docstring = (
                entry.get("docstring")
                or entry.get("detailed_description")
                or entry.get("short_description")
                or ""
            )
            if self._looks_like_source_code(docstring):
                weaknesses.append(
                    Weakness(
                        artifact="doc_artifacts.json",
                        entry_id=entry_id,
                        field="docstring",
                        severity=Severity.CRITICAL,
                        message=f"Entry '{entry_id}': docstring field appears to contain raw source code",
                    )
                )

            # Collect for duplicate detection
            normalized_ds = docstring.strip()
            if normalized_ds:
                docstring_map.setdefault(normalized_ds, []).append(entry_id)

            # CRITICAL: module-level docstring misassigned to a function entry
            entry_type = (entry.get("type") or "").lower()
            if entry_type in {"function", "method", "classmethod", "staticmethod"}:
                if self._looks_like_module_docstring(docstring):
                    weaknesses.append(
                        Weakness(
                            artifact="doc_artifacts.json",
                            entry_id=entry_id,
                            field="docstring",
                            severity=Severity.CRITICAL,
                            message=(
                                f"Entry '{entry_id}': module-level docstring appears to be "
                                "misassigned to a function entry"
                            ),
                        )
                    )

            # MAJOR: missing required enrichment fields
            for field in (
                "business_context",
                "parameters",
                "returns",
                "raises",
                "side_effects",
                "pipeline_stage",
            ):
                val = entry.get(field)
                if val is None or val == "" or val == [] or val == {}:
                    weaknesses.append(
                        Weakness(
                            artifact="doc_artifacts.json",
                            entry_id=entry_id,
                            field=field,
                            severity=Severity.MAJOR,
                            message=f"Entry '{entry_id}': missing field '{field}'",
                        )
                    )

            # MINOR: optional fields
            for field in ("dependencies", "signature", "type"):
                val = entry.get(field)
                if val is None or val == "" or val == []:
                    weaknesses.append(
                        Weakness(
                            artifact="doc_artifacts.json",
                            entry_id=entry_id,
                            field=field,
                            severity=Severity.MINOR,
                            message=f"Entry '{entry_id}': missing optional field '{field}'",
                        )
                    )

        # CRITICAL: identical docstrings
        for docstring, ids in docstring_map.items():
            if len(ids) > 1:
                weaknesses.append(
                    Weakness(
                        artifact="doc_artifacts.json",
                        entry_id=", ".join(str(i) for i in ids[:5]),
                        field="docstring",
                        severity=Severity.CRITICAL,
                        message=(
                            f"Identical docstring copy-pasted across {len(ids)} entries: "
                            f"{ids[:3]}"
                        ),
                    )
                )

        return weaknesses

    def _check_ast(self, data: Any) -> List[Weakness]:
        weaknesses: List[Weakness] = []

        if not isinstance(data, dict):
            return weaknesses

        for file_key, file_data in data.items():
            if not isinstance(file_data, dict):
                continue

            functions = file_data.get("functions") or []
            classes = file_data.get("classes") or []

            # CRITICAL: entries with no resolvable name
            for sym in functions + classes:
                if isinstance(sym, dict):
                    name = sym.get("name", "")
                    if not name or str(name).lower() in {"unknown", "none"}:
                        weaknesses.append(
                            Weakness(
                                artifact="ast.json",
                                entry_id=file_key,
                                field="name",
                                severity=Severity.CRITICAL,
                                message=(
                                    f"File '{file_key}': symbol has no resolvable name"
                                ),
                            )
                        )

            # CRITICAL: file with empty functions[] and classes[]
            if not functions and not classes:
                weaknesses.append(
                    Weakness(
                        artifact="ast.json",
                        entry_id=file_key,
                        severity=Severity.CRITICAL,
                        message=(
                            f"File '{file_key}' has empty functions[] and classes[] "
                            "— likely a parsing gap"
                        ),
                    )
                )

            # MAJOR: missing semantic metadata fields
            for field in ("semantic_role", "layer", "return_type"):
                if not file_data.get(field):
                    weaknesses.append(
                        Weakness(
                            artifact="ast.json",
                            entry_id=file_key,
                            field=field,
                            severity=Severity.MAJOR,
                            message=f"File '{file_key}': missing field '{field}'",
                        )
                    )

        return weaknesses

    def _check_dependencies(self, data: Any) -> List[Weakness]:
        weaknesses: List[Weakness] = []

        edges: List[Any] = []
        if isinstance(data, dict):
            edges = data.get("edges") or []
        elif isinstance(data, list):
            edges = data

        for idx, edge in enumerate(edges):
            if not isinstance(edge, dict):
                continue

            # CRITICAL: unexplained prefixes such as "runtime:"
            for field in ("from", "to", "id"):
                val = edge.get(field, "") or ""
                match = re.match(r"^([a-zA-Z_]+):", val)
                if match:
                    prefix = match.group(1)
                    if prefix not in {"http", "https", "file"}:
                        weaknesses.append(
                            Weakness(
                                artifact="dependencies_normalized.json",
                                entry_id=str(idx),
                                field=field,
                                severity=Severity.CRITICAL,
                                message=(
                                    f"Edge [{idx}].{field}='{val}' has unexplained prefix "
                                    f"'{prefix}:' — no schema legend found"
                                ),
                            )
                        )

            # MAJOR: external deps without version or purpose
            kind = (edge.get("kind") or edge.get("type") or "").lower()
            if "external" in kind:
                if not edge.get("version"):
                    weaknesses.append(
                        Weakness(
                            artifact="dependencies_normalized.json",
                            entry_id=str(idx),
                            field="version",
                            severity=Severity.MAJOR,
                            message=f"External dependency at index {idx} has no version noted",
                        )
                    )
                if not edge.get("purpose"):
                    weaknesses.append(
                        Weakness(
                            artifact="dependencies_normalized.json",
                            entry_id=str(idx),
                            field="purpose",
                            severity=Severity.MAJOR,
                            message=f"External dependency at index {idx} has no purpose noted",
                        )
                    )

        return weaknesses

    def _check_components(self, data: Any) -> List[Weakness]:
        weaknesses: List[Weakness] = []

        components: List[Any] = []
        if isinstance(data, list):
            components = data
        elif isinstance(data, dict):
            components = data.get("components") or []

        _generic_names = {"component", "module", "service", "layer", "unit", ""}

        for idx, comp in enumerate(components):
            if not isinstance(comp, dict):
                continue

            name = (comp.get("name") or "").strip().lower()
            comp_id = comp.get("component_id") or comp.get("name") or f"[{idx}]"

            # MAJOR: generic component name
            if name in _generic_names:
                weaknesses.append(
                    Weakness(
                        artifact="components.json",
                        entry_id=str(comp_id),
                        field="name",
                        severity=Severity.MAJOR,
                        message=f"Component '{comp_id}' has a generic or missing name",
                    )
                )

            # MAJOR: missing business_role
            if not comp.get("business_role"):
                weaknesses.append(
                    Weakness(
                        artifact="components.json",
                        entry_id=str(comp_id),
                        field="business_role",
                        severity=Severity.MAJOR,
                        message=f"Component '{comp_id}' is missing 'business_role'",
                    )
                )

            # MAJOR: missing architectural_layer
            if not comp.get("architectural_layer"):
                weaknesses.append(
                    Weakness(
                        artifact="components.json",
                        entry_id=str(comp_id),
                        field="architectural_layer",
                        severity=Severity.MAJOR,
                        message=f"Component '{comp_id}' is missing 'architectural_layer'",
                    )
                )

        return weaknesses

    def _check_edge_cases(self, data: Any) -> List[Weakness]:
        weaknesses: List[Weakness] = []

        results: Any = data
        if isinstance(data, dict):
            results = data.get("results") or data.get("edge_cases") or data

        # MAJOR: completely empty results with no detection_ran flag
        is_empty = (
            (isinstance(results, list) and len(results) == 0)
            or (isinstance(results, dict) and not any(results.values()))
        )
        if is_empty:
            if isinstance(data, dict) and "detection_ran" not in data:
                weaknesses.append(
                    Weakness(
                        artifact="edge_cases.json",
                        severity=Severity.MAJOR,
                        message=(
                            "edge_cases.json has empty results and no 'detection_ran' boolean "
                            "— cannot distinguish 'no issues' from 'detection did not run'"
                        ),
                    )
                )

        # MAJOR: missing anomaly categories
        if isinstance(data, dict):
            expected_categories = {
                "circular_imports",
                "monolithic_files",
                "generated_code",
            }
            for cat in expected_categories:
                if cat not in data:
                    weaknesses.append(
                        Weakness(
                            artifact="edge_cases.json",
                            field=cat,
                            severity=Severity.MAJOR,
                            message=(
                                f"edge_cases.json is missing anomaly category '{cat}'"
                            ),
                        )
                    )

        return weaknesses

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _load_json(path: Path) -> Optional[Any]:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    _CODE_PATTERNS = re.compile(
        r"def\s+\w+\s*\(|class\s+\w+[:\(]|import\s+\w+|from\s+\w+\s+import|"
        r"\bif\s+\w+.*:\s*$|\bfor\s+\w+\s+in\s+",
        re.MULTILINE,
    )

    @classmethod
    def _looks_like_source_code(cls, text: str) -> bool:
        """Return True when *text* appears to contain raw Python source code."""
        if not text:
            return False
        return bool(cls._CODE_PATTERNS.search(text))

    _MODULE_DOC_PATTERNS = re.compile(
        r"(module|package|this\s+module|this\s+package|provides|overview|pipeline)\b",
        re.IGNORECASE,
    )

    @classmethod
    def _looks_like_module_docstring(cls, text: str) -> bool:
        """Return True when *text* reads like a file-level module docstring."""
        if not text or len(text) < 40:
            return False
        return bool(cls._MODULE_DOC_PATTERNS.search(text[:200]))
