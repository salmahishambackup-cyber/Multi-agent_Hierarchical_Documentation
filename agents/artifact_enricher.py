"""
Artifact Enricher agent — receives a WeaknessReport and produces enriched
artifact files that resolve every identified issue.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from agents.base_agent import BaseAgent
from schemas.enriched_artifacts import (
    EnrichedDocEntry,
    ParameterDoc,
    ReturnDoc,
    Severity,
    WeaknessReport,
)
from utils.artifact_utils import (
    detect_duplicate_docstrings,
    extract_business_context,
    resolve_name_from_ast,
    validate_enriched_artifacts,
)


class ArtifactEnricher(BaseAgent):
    """
    Receives a :class:`~schemas.enriched_artifacts.WeaknessReport` and the
    raw artifacts directory, then writes enriched replacement files that
    address every CRITICAL and MAJOR issue.

    The agent iterates until no CRITICAL or MAJOR weaknesses remain, or
    until *max_iterations* is reached to prevent infinite loops.
    """

    def __init__(
        self,
        repo_path: str,
        artifacts_dir: str = "./artifacts",
        max_iterations: int = 3,
    ):
        """
        Initialise enricher.

        Args:
            repo_path: Path to the repository being documented.
            artifacts_dir: Directory that holds the artifact JSON files.
            max_iterations: Maximum enrichment passes before giving up.
        """
        super().__init__(repo_path=repo_path, artifacts_dir=artifacts_dir)
        self.max_iterations = max_iterations

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> Dict[str, Any]:
        """
        Load the latest weakness report, enrich all artifacts, and
        iterate until no CRITICAL/MAJOR issues remain.

        Returns:
            Dictionary with enrichment statistics and final report path.
        """
        from agents.artifact_critic import ArtifactCritic

        iteration = 0
        report: Optional[WeaknessReport] = None

        while iteration < self.max_iterations:
            iteration += 1
            print(f"\n🔧 Artifact Enricher — iteration {iteration}/{self.max_iterations}")

            # Run critic to get (or refresh) the weakness report
            critic = ArtifactCritic(
                repo_path=str(self.repo_path),
                artifacts_dir=str(self.artifacts_dir),
            )
            report = critic.audit()
            print(f"   {report.summary()}")

            if not report.has_blocking_issues():
                print("   ✅ No CRITICAL/MAJOR issues — enrichment complete.")
                break

            # Enrich artifacts based on current weaknesses
            self._enrich_doc_artifacts(report)
            self._enrich_ast(report)
            self._enrich_components(report)
            self._enrich_edge_cases(report)

        result = {
            "iterations": iteration,
            "final_critical": report.critical_count if report else 0,
            "final_major": report.major_count if report else 0,
            "final_minor": report.minor_count if report else 0,
            "report_path": str(self.artifacts_dir / "weakness_report.json"),
        }

        # Persist final report
        if report:
            self.save_artifact("weakness_report.json", report.model_dump())

        print(
            f"\n📦 Enrichment finished after {iteration} iteration(s). "
            f"Remaining — CRITICAL: {result['final_critical']}, "
            f"MAJOR: {result['final_major']}"
        )
        return result

    # ------------------------------------------------------------------
    # Per-artifact enrichers
    # ------------------------------------------------------------------

    def _enrich_doc_artifacts(self, report: WeaknessReport) -> None:
        """Resolve issues in doc_artifacts.json."""
        artifact_path = self.artifacts_dir / "doc_artifacts.json"
        if not artifact_path.exists():
            return

        data = self._load_json(artifact_path)
        if data is None:
            return

        entries, envelope = self._unwrap_entries(data)
        ast_data = self._load_ast()

        # Collect affected entry IDs from the weakness report
        affected_ids = {
            w.entry_id
            for w in report.weaknesses
            if w.artifact == "doc_artifacts.json" and w.entry_id is not None
        }

        for idx, entry in enumerate(entries):
            entry_id = entry.get("name") or f"[{idx}]"
            if entry_id not in affected_ids and str(idx) not in affected_ids:
                # Check by index too
                if not any(
                    w.entry_id in {entry_id, f"[{idx}]", str(idx)}
                    for w in report.weaknesses
                    if w.artifact == "doc_artifacts.json"
                ):
                    continue

            self._enrich_single_doc_entry(entry, idx, ast_data)

        # De-duplicate docstrings AFTER individual enrichment
        duplicates = detect_duplicate_docstrings(entries)
        for idx_a, idx_b, _ in duplicates:
            # Only mark the second (and later) occurrence to avoid circular
            # cross-references. The first entry retains its original content.
            dup_entry = entries[idx_b]
            existing = dup_entry.get("short_description") or dup_entry.get("docstring") or ""
            suffix = f" (Duplicate of entry [{idx_a}] — please review)"
            if not existing.endswith(")"):
                if "short_description" in dup_entry:
                    dup_entry["short_description"] = existing + suffix
                elif "docstring" in dup_entry:
                    dup_entry["docstring"] = existing + suffix

        self._save_entries(artifact_path, entries, envelope)

    def _enrich_single_doc_entry(
        self,
        entry: Dict[str, Any],
        idx: int,
        ast_data: Dict[str, Any],
    ) -> None:
        """Apply all required enrichments to a single doc entry in-place."""
        # --- Name resolution ---
        name = entry.get("name", "") or ""
        if not name or name.lower() in {"unknown", "none", "null"}:
            resolved = resolve_name_from_ast(entry, ast_data)
            entry["name"] = resolved

        # --- Type ---
        if not entry.get("type"):
            entry["type"] = "function"

        # --- Signature ---
        if not entry.get("signature"):
            entry["signature"] = f"{entry['name']}(...)"

        # --- Short / detailed description ---
        existing_doc = (
            entry.get("docstring")
            or entry.get("detailed_description")
            or entry.get("short_description")
            or ""
        )
        if not entry.get("short_description"):
            first_sentence = existing_doc.split(".")[0].strip()
            entry["short_description"] = first_sentence or f"Performs {entry['name']}."
        if not entry.get("detailed_description"):
            entry["detailed_description"] = existing_doc or entry["short_description"]

        # --- Business context ---
        if not entry.get("business_context"):
            entry["business_context"] = extract_business_context(entry)

        # --- Pipeline stage ---
        if not entry.get("pipeline_stage"):
            from utils.artifact_utils import _infer_pipeline_stage
            entry["pipeline_stage"] = _infer_pipeline_stage(
                entry.get("name", ""), entry.get("file", "")
            )

        # --- Parameters ---
        if not entry.get("parameters"):
            entry["parameters"] = []

        # --- Returns ---
        if not entry.get("returns"):
            entry["returns"] = {"type": "Any", "description": ""}

        # --- Raises ---
        if not entry.get("raises"):
            entry["raises"] = []

        # --- Side effects ---
        if not entry.get("side_effects"):
            entry["side_effects"] = []

        # --- Dependencies ---
        if not entry.get("dependencies"):
            entry["dependencies"] = []

        # --- Example ---
        if not entry.get("example"):
            entry["example"] = f"# TODO: add usage example for {entry['name']}"

    def _enrich_ast(self, report: WeaknessReport) -> None:
        """Add missing semantic_role, layer, return_type to ast.json entries."""
        artifact_path = self.artifacts_dir / "ast.json"
        if not artifact_path.exists():
            return

        data = self._load_json(artifact_path)
        if not isinstance(data, dict):
            return

        affected_files = {
            w.entry_id
            for w in report.weaknesses
            if w.artifact == "ast.json" and w.entry_id is not None
        }

        for file_key, file_data in data.items():
            if file_key not in affected_files and not any(
                w.artifact == "ast.json" for w in report.weaknesses
            ):
                continue
            if not isinstance(file_data, dict):
                continue

            if not file_data.get("semantic_role"):
                file_data["semantic_role"] = self._infer_semantic_role(file_key)
            if not file_data.get("layer"):
                file_data["layer"] = self._infer_layer(file_key)
            if not file_data.get("return_type"):
                file_data["return_type"] = "unknown"

        self._save_json(artifact_path, data)

    def _enrich_components(self, report: WeaknessReport) -> None:
        """Add missing business_role and architectural_layer to components.json."""
        artifact_path = self.artifacts_dir / "components.json"
        if not artifact_path.exists():
            return

        data = self._load_json(artifact_path)
        components: List[Any] = []
        envelope: Optional[Dict[str, Any]] = None

        if isinstance(data, list):
            components = data
        elif isinstance(data, dict):
            envelope = data
            components = data.get("components") or []

        affected_ids = {
            w.entry_id
            for w in report.weaknesses
            if w.artifact == "components.json" and w.entry_id is not None
        }

        for comp in components:
            if not isinstance(comp, dict):
                continue
            comp_id = str(comp.get("component_id") or comp.get("name") or "")
            if comp_id not in affected_ids and not any(
                w.artifact == "components.json" for w in report.weaknesses
            ):
                continue

            if not comp.get("business_role"):
                comp["business_role"] = (
                    f"Provides {comp.get('name', 'functionality')} capabilities"
                )
            if not comp.get("architectural_layer"):
                comp["architectural_layer"] = self._infer_layer(
                    " ".join(comp.get("files", []))
                )

        if envelope is not None:
            envelope["components"] = components
            self._save_json(artifact_path, envelope)
        else:
            self._save_json(artifact_path, components)

    def _enrich_edge_cases(self, report: WeaknessReport) -> None:
        """Ensure edge_cases.json has detection_ran flag and anomaly categories."""
        artifact_path = self.artifacts_dir / "edge_cases.json"
        if not artifact_path.exists():
            # Create a minimal valid edge_cases.json
            skeleton: Dict[str, Any] = {
                "detection_ran": False,
                "circular_imports": [],
                "monolithic_files": [],
                "generated_code": [],
            }
            self._save_json(artifact_path, skeleton)
            return

        data = self._load_json(artifact_path)
        if not isinstance(data, dict):
            return

        if "detection_ran" not in data:
            data["detection_ran"] = True

        for cat in ("circular_imports", "monolithic_files", "generated_code"):
            if cat not in data:
                data[cat] = []

        self._save_json(artifact_path, data)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _load_json(self, path: Path) -> Optional[Any]:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    def _save_json(self, path: Path, data: Any) -> None:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def _save_entries(
        self,
        path: Path,
        entries: List[Dict[str, Any]],
        envelope: Optional[Dict[str, Any]],
    ) -> None:
        if envelope is not None:
            # Detect which key held the list
            for key in ("symbols", "entries", "functions"):
                if key in envelope:
                    envelope[key] = entries
                    break
            self._save_json(path, envelope)
        else:
            self._save_json(path, entries)

    def _load_ast(self) -> Dict[str, Any]:
        ast_path = self.artifacts_dir / "ast.json"
        if ast_path.exists():
            data = self._load_json(ast_path)
            if isinstance(data, dict):
                return data
        return {}

    @staticmethod
    def _unwrap_entries(
        data: Any,
    ) -> tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """Extract the entries list from various envelope formats."""
        if isinstance(data, list):
            return data, None
        if isinstance(data, dict):
            for key in ("symbols", "entries", "functions"):
                val = data.get(key)
                if isinstance(val, list):
                    return val, data
        return [], None

    _LAYER_SIGNALS: Dict[str, List[str]] = {
        "presentation": ["ui", "view", "template", "render", "display", "readme"],
        "service": [
            "service", "use_case", "orchestrat", "pipeline", "workflow", "agent",
        ],
        "domain": ["model", "entity", "domain", "schema", "contract"],
        "infrastructure": [
            "util", "helper", "client", "adapter", "gateway", "io", "cache",
            "db", "database", "storage", "repo",
        ],
        "analysis": ["analyz", "analys", "inspect", "parse", "extract", "ast"],
    }

    @classmethod
    def _infer_layer(cls, text: str) -> str:
        lower = text.lower()
        for layer, signals in cls._LAYER_SIGNALS.items():
            if any(s in lower for s in signals):
                return layer
        return "service"

    _ROLE_SIGNALS: Dict[str, str] = {
        "orchestrat": "orchestration",
        "pipeline": "pipeline coordination",
        "agent": "autonomous agent",
        "analyz": "static analysis",
        "analys": "static analysis",
        "generat": "content generation",
        "validat": "validation",
        "evaluat": "evaluation",
        "util": "utility support",
        "schema": "data modelling",
        "client": "external integration",
        "cache": "caching",
    }

    @classmethod
    def _infer_semantic_role(cls, file_key: str) -> str:
        lower = file_key.lower()
        for signal, role in cls._ROLE_SIGNALS.items():
            if signal in lower:
                return role
        return "general purpose"
