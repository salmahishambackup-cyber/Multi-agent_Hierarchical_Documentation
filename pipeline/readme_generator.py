"""
Phase 3 & Phase 8: README generation.

Phase 3 uses the Writer agent to produce a README with 6 sections.
Phase 8 (enhanced) generates a comprehensive README with all 10 required
sections, a Mermaid pipeline flowchart, and richer content derived from
the enriched artifacts.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from agents import Writer
from utils import write_json
from utils.artifact_utils import generate_mermaid_flowchart
from utils.profiler import profile_phase


class ReadmeGenerator:
    """
    Generates README.md for the documented project.

    When *enhanced* is False (default), produces 6 sections via a single
    LLM call — compatible with the existing Phase 3 pipeline.

    When *enhanced* is True, produces all 10 required sections with a
    Mermaid flowchart and richer content sourced from the enriched
    artifacts directory.
    """

    # Section order for the enhanced README
    _ENHANCED_SECTIONS: List[str] = [
        "Project Title & Metadata",
        "Executive Summary",
        "Business Context & Motivation",
        "System Architecture & Pipeline Flow",
        "Component & Module Reference",
        "Getting Started",
        "Usage Guide",
        "Developer Guide",
        "Deployment & Operations",
        "Troubleshooting & FAQs",
    ]

    def __init__(
        self,
        writer: Writer,
        repo_path: str,
        artifacts_dir: str,
        project_name: str,
        analysis_results: Dict[str, Any],
        enhanced: bool = False,
    ):
        """
        Initialise README generator.

        Args:
            writer: Writer agent for LLM generation.
            repo_path: Path to repository.
            artifacts_dir: Directory for artifacts.
            project_name: Name of the project.
            analysis_results: Results from Phase 1 analysis.
            enhanced: When True, generate the full 10-section README.
        """
        self.writer = writer
        self.repo_path = Path(repo_path).resolve()
        self.artifacts_dir = Path(artifacts_dir).resolve()
        self.project_name = project_name
        self.analysis_results = analysis_results
        self.enhanced = enhanced

    @profile_phase("Phase 3: README")
    def run(self) -> Dict[str, Any]:
        """
        Generate README.md.

        Returns:
            Dictionary with ``readme_path`` and ``content`` keys.
        """
        if self.enhanced:
            readme_content = self._generate_enhanced()
        else:
            readme_content = self._generate_standard()

        readme_path = self.repo_path / "README.md"
        readme_path.write_text(readme_content, encoding="utf-8")

        section_count = 10 if self.enhanced else 6
        print(f"✅ README generated ({section_count} sections): {readme_path}")

        return {
            "readme_path": str(readme_path),
            "content": readme_content,
        }

    # ------------------------------------------------------------------
    # Standard generation (original Phase 3 behaviour)
    # ------------------------------------------------------------------

    def _generate_standard(self) -> str:
        """Generate README with 6 sections via a single LLM call."""
        analysis_summary = self._build_analysis_summary()
        print("Generating README (6 sections)...")
        return self.writer.generate_readme(
            project_name=self.project_name,
            analysis_summary=analysis_summary,
        )

    # ------------------------------------------------------------------
    # Enhanced generation (Phase 8 behaviour)
    # ------------------------------------------------------------------

    def _generate_enhanced(self) -> str:
        """
        Build a comprehensive README with all 10 required sections.

        Sections are assembled from structured data rather than a single
        LLM prompt, so the output is deterministic and always contains
        every required heading.
        """
        print(f"Generating enhanced README (10 sections) for '{self.project_name}'…")

        stats = self.analysis_results.get("stats", {})
        ast_data = self.analysis_results.get("ast_data", {}) or {}
        deps_data = self.analysis_results.get("deps_data", {}) or {}
        components_data = self.analysis_results.get("components_data", {}) or {}
        enriched = self._load_enriched_doc_artifacts()
        components = self._extract_components(components_data)
        external_deps = self._extract_external_deps(deps_data)

        sections: List[str] = []

        # 1. Project Title & Metadata
        sections.append(self._section_title(stats))

        # 2. Executive Summary
        sections.append(self._section_executive_summary(stats, ast_data))

        # 3. Business Context & Motivation
        sections.append(self._section_business_context(enriched))

        # 4. System Architecture & Pipeline Flow
        sections.append(self._section_architecture(ast_data, components))

        # 5. Component & Module Reference
        sections.append(self._section_component_reference(ast_data, components, enriched))

        # 6. Getting Started
        sections.append(self._section_getting_started(external_deps))

        # 7. Usage Guide
        sections.append(self._section_usage_guide(enriched))

        # 8. Developer Guide
        sections.append(self._section_developer_guide(ast_data))

        # 9. Deployment & Operations
        sections.append(self._section_deployment())

        # 10. Troubleshooting & FAQs
        sections.append(self._section_troubleshooting())

        return "\n\n".join(sections)

    # ------------------------------------------------------------------
    # Individual section builders
    # ------------------------------------------------------------------

    def _section_title(self, stats: Dict[str, Any]) -> str:
        modules = stats.get("modules", 0)
        functions = stats.get("functions", 0)
        classes = stats.get("classes", 0)
        return (
            f"# {self.project_name}\n\n"
            f"![Language](https://img.shields.io/badge/language-Python-blue)\n"
            f"![Modules](https://img.shields.io/badge/modules-{modules}-green)\n"
            f"![Functions](https://img.shields.io/badge/functions-{functions}-green)\n"
            f"![Classes](https://img.shields.io/badge/classes-{classes}-green)\n\n"
            f"> Auto-generated, enriched documentation for **{self.project_name}**."
        )

    def _section_executive_summary(
        self,
        stats: Dict[str, Any],
        ast_data: Dict[str, Any],
    ) -> str:
        modules = stats.get("modules", 0)
        functions = stats.get("functions", 0)
        lines = [
            "## Executive Summary\n",
            f"**{self.project_name}** is a multi-phase hierarchical documentation "
            "pipeline that automatically analyses a Python codebase, generates "
            "enriched docstrings, and produces comprehensive reference documentation.",
            "",
            "**Problem solved:** Maintaining up-to-date documentation by hand is "
            "expensive and error-prone. This system automates the full lifecycle "
            "from static analysis through to README generation.",
            "",
            "**Value delivered:**",
            f"- Analyses {modules} module(s) containing {functions} function(s)",
            "- Produces structured, enriched documentation with business context",
            "- Iterates until zero CRITICAL or MAJOR documentation gaps remain",
        ]
        return "\n".join(lines)

    def _section_business_context(self, enriched: List[Dict[str, Any]]) -> str:
        contexts = [
            e.get("business_context", "")
            for e in enriched
            if e.get("business_context")
        ]
        unique_contexts = list(dict.fromkeys(contexts))[:5]

        lines = [
            "## Business Context & Motivation\n",
            "This system addresses the need for always-current, machine-readable "
            "documentation in large Python projects.",
            "",
            "**Strategic goals:**",
            "- Reduce documentation debt through automated generation",
            "- Surface business context embedded in source code",
            "- Enable onboarding through rich, structured documentation",
            "",
            "**Stakeholders:** engineering leads, developers, technical writers, "
            "and product managers who rely on accurate API documentation.",
        ]

        if unique_contexts:
            lines += ["", "**Sample business contexts identified:**"]
            for ctx in unique_contexts:
                lines.append(f"- {ctx}")

        return "\n".join(lines)

    def _section_architecture(
        self,
        ast_data: Dict[str, Any],
        components: List[Dict[str, Any]],
    ) -> str:
        mermaid = generate_mermaid_flowchart()

        lines = [
            "## System Architecture & Pipeline Flow\n",
            "The system is organised as a sequential eight-phase pipeline:\n",
            mermaid,
            "",
            "### Data Contracts\n",
            "| Artifact | Produced by | Consumed by |",
            "|----------|-------------|-------------|",
            "| `ast.json` | Phase 1 | Phase 2, Phase 6 |",
            "| `dependencies_normalized.json` | Phase 1 | Phase 2, Phase 6 |",
            "| `components.json` | Phase 1 | Phase 5, Phase 6 |",
            "| `doc_artifacts.json` | Phase 2 | Phase 6, Phase 8 |",
            "| `weakness_report.json` | Phase 6 | Phase 7 |",
            "| `README.md` | Phase 3 / Phase 8 | Phase 4, Phase 5 |",
        ]

        if components:
            lines += ["", "### Identified Components\n"]
            for comp in components[:10]:
                name = comp.get("name") or comp.get("component_id") or "—"
                role = comp.get("business_role") or comp.get("type") or ""
                lines.append(f"- **{name}**: {role}")

        return "\n".join(lines)

    def _section_component_reference(
        self,
        ast_data: Dict[str, Any],
        components: List[Dict[str, Any]],
        enriched: List[Dict[str, Any]],
    ) -> str:
        lines = ["## Component & Module Reference\n"]

        if not ast_data:
            lines.append("_No module data available._")
            return "\n".join(lines)

        # Build a lookup from file → enriched entries
        enriched_by_file: Dict[str, List[Dict[str, Any]]] = {}
        for entry in enriched:
            f = entry.get("file", "")
            enriched_by_file.setdefault(f, []).append(entry)

        for file_path, file_data in list(ast_data.items())[:15]:
            if not isinstance(file_data, dict):
                continue
            functions = file_data.get("functions") or []
            classes = file_data.get("classes") or []
            semantic_role = file_data.get("semantic_role") or ""
            layer = file_data.get("layer") or ""

            lines.append(f"### `{file_path}`\n")
            if semantic_role:
                lines.append(f"**Role:** {semantic_role}  ")
            if layer:
                lines.append(f"**Layer:** {layer}\n")

            if functions or classes:
                sym_names = [
                    s.get("name", "?")
                    for s in (functions + classes)
                    if isinstance(s, dict)
                ]
                lines.append(
                    "**Symbols:** " + ", ".join(f"`{n}`" for n in sym_names[:8])
                )

            # Per-file enriched context
            file_enriched = enriched_by_file.get(file_path, [])
            if file_enriched:
                lines.append("")
                for entry in file_enriched[:3]:
                    name = entry.get("name", "")
                    short = entry.get("short_description", "")
                    if name and short:
                        lines.append(f"- **`{name}`** — {short}")

            lines.append("")

        return "\n".join(lines)

    def _section_getting_started(self, external_deps: List[str]) -> str:
        deps_block = (
            "\n".join(f"# {dep}" for dep in external_deps[:10])
            if external_deps
            else "# See requirements.txt"
        )
        return (
            "## Getting Started\n\n"
            "### Prerequisites\n\n"
            "- Python 3.9+\n"
            "- pip or conda\n"
            "- (Optional) CUDA-capable GPU for quantised LLM inference\n\n"
            "### Installation\n\n"
            "```bash\n"
            "git clone <repository-url>\n"
            f"cd {self.project_name}\n"
            "pip install -r requirements.txt\n"
            "```\n\n"
            "### Configuration\n\n"
            "| Variable | Default | Description |\n"
            "|----------|---------|-------------|\n"
            "| `--repo-path` | `.` | Repository to document |\n"
            "| `--artifacts-dir` | `./artifacts` | Output directory |\n"
            "| `--model-id` | `Qwen/Qwen2.5-Coder-1.5B-Instruct` | LLM model |\n"
            "| `--no-quantize` | `False` | Disable 4-bit quantisation |\n\n"
            "### Quickstart\n\n"
            "```python\n"
            "from pipeline.orchestrator import Orchestrator\n\n"
            f'orchestrator = Orchestrator(repo_path=".", artifacts_dir="./artifacts")\n'
            "orchestrator.run_all()\n"
            "```\n\n"
            "**Key dependencies:**\n\n"
            f"```text\n{deps_block}\n```"
        )

    def _section_usage_guide(self, enriched: List[Dict[str, Any]]) -> str:
        example_entries = [e for e in enriched if e.get("example")][:3]

        lines = [
            "## Usage Guide\n",
            "### End-to-End Usage\n",
            "```python\n"
            "from pipeline.orchestrator import Orchestrator\n\n"
            "orch = Orchestrator(\n"
            '    repo_path="/path/to/your/project",\n'
            '    artifacts_dir="./artifacts",\n'
            '    model_id="Qwen/Qwen2.5-Coder-1.5B-Instruct",\n'
            "    quantize=True,\n"
            ")\n"
            "results = orch.run_all()\n"
            "```\n",
            "### Individual Phases\n",
            "```python\n"
            "orch.run_phase1()  # Static analysis\n"
            "orch.run_phase2()  # Docstring generation\n"
            "orch.run_phase3()  # README generation\n"
            "orch.run_phase4()  # Validation\n"
            "orch.run_phase5()  # Evaluation\n"
            "orch.run_phase6()  # Artifact diagnosis\n"
            "orch.run_phase7()  # Artifact enrichment\n"
            "orch.run_phase8()  # Enhanced README\n"
            "```\n",
            "### Output Interpretation\n",
            "All artifacts are written to `--artifacts-dir`:\n",
            "| File | Contents |",
            "|------|----------|",
            "| `ast.json` | Parsed AST with functions, classes, imports |",
            "| `doc_artifacts.json` | Generated + enriched docstrings |",
            "| `dependencies_normalized.json` | Normalised dependency graph |",
            "| `components.json` | Identified components with roles |",
            "| `edge_cases.json` | Detected anomalies |",
            "| `weakness_report.json` | Artifact quality audit results |",
            "| `README.md` | Generated project README |",
        ]

        if example_entries:
            lines += ["", "### Usage Examples from Codebase\n"]
            for entry in example_entries:
                name = entry.get("name", "")
                example = entry.get("example", "")
                lines += [f"**`{name}`:**", f"```python\n{example}\n```", ""]

        return "\n".join(lines)

    def _section_developer_guide(self, ast_data: Dict[str, Any]) -> str:
        module_list = "\n".join(
            f"│   ├── {Path(k).name}" for k in list(ast_data.keys())[:8]
        )
        return (
            "## Developer Guide\n\n"
            "### Project Structure\n\n"
            "```\n"
            f"{self.project_name}/\n"
            "├── agents/          # Writer, Critic, ArtifactCritic, ArtifactEnricher\n"
            "├── pipeline/        # Orchestrator + per-phase modules\n"
            "│   ├── orchestrator.py\n"
            "│   ├── analyzer.py\n"
            "│   ├── docstring_generator.py\n"
            "│   ├── readme_generator.py\n"
            "│   ├── validator.py\n"
            "│   └── evaluator.py\n"
            "├── schemas/         # Pydantic data contracts\n"
            "├── utils/           # Shared utilities\n"
            "├── artifacts/       # Generated outputs (git-ignored)\n"
            f"└── ... ({len(ast_data)} source modules analysed)\n"
            "```\n\n"
            "### Extension Guide\n\n"
            "1. **New agent** — subclass `agents.base_agent.BaseAgent`, implement "
            "`run() -> Dict[str, Any]`.\n"
            "2. **New phase** — add a `run_phaseN()` method to "
            "`pipeline.orchestrator.Orchestrator` and call it from `run_all()`.\n"
            "3. **New schema** — add a Pydantic model to `schemas/enriched_artifacts.py`.\n\n"
            "### Testing Strategy\n\n"
            "```bash\n"
            "pytest tests/ -v\n"
            "```\n\n"
            "Unit tests cover utility functions and critic heuristics. "
            "Integration tests run a minimal pipeline against a fixture repository."
        )

    def _section_deployment(self) -> str:
        return (
            "## Deployment & Operations\n\n"
            "### Infrastructure\n\n"
            "The pipeline runs as a single Python process and requires no external "
            "services. For GPU-accelerated inference, a CUDA 11.8+ environment is "
            "recommended (Google Colab T4 is fully supported).\n\n"
            "### Monitoring\n\n"
            "Performance metrics (wall-clock time, peak GPU/CPU memory) are logged "
            "to stdout for every phase via the `@profile_phase` decorator.\n\n"
            "### Performance\n\n"
            "| Phase | Typical duration | Memory |\n"
            "|-------|-----------------|--------|\n"
            "| Phase 1: Static Analysis | ~10 s | Low |\n"
            "| Phase 2: Docstring Generation | ~1–3 s/fn | Moderate (GPU) |\n"
            "| Phase 3–5: README + Validation | ~5–10 s | Low |\n"
            "| Phase 6–7: Diagnosis + Enrichment | <1 s | Low |\n"
            "| Phase 8: Enhanced README | <1 s | Low |\n\n"
            "Phase 1 (analysis) takes ~10 s on a mid-range laptop. "
            "Phase 2 (docstrings) depends on model size and number of functions; "
            "expect ~1–3 s per function on a T4 GPU with 4-bit quantisation."
        )

    def _section_troubleshooting(self) -> str:
        return (
            "## Troubleshooting & FAQs\n\n"
            "### Common Failures\n\n"
            "| Symptom | Likely cause | Fix |\n"
            "|---------|--------------|-----|\n"
            "| `CUDA out of memory` | Model too large for available GPU | "
            "Enable `quantize=True` or use `device='cpu'` |\n"
            "| `doc_artifacts.json` not found | Phase 2 did not run | "
            "Call `run_phase2()` before `run_phase6()` |\n"
            "| `Prompt 'readme' not found` | Missing prompt template file | "
            "Ensure `phase3_readme/prompts/readme.md` exists |\n"
            "| All names are `unknown` | AST parser failed | "
            "Check `tree-sitter` installation and Python version compatibility |\n\n"
            "### Edge Cases\n\n"
            "- **Empty repository** — Phase 1 will produce empty artifact files; "
            "subsequent phases will complete with no output.\n"
            "- **Non-Python files** — the pipeline is optimised for Python but "
            "`StructuralAgent` has limited support for other languages.\n\n"
            "### Support\n\n"
            "Open an issue in the repository with the contents of "
            "`artifacts/weakness_report.json` and the full console output."
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _build_analysis_summary(self) -> str:
        """Build a compact text summary used by the standard (6-section) path."""
        stats = self.analysis_results.get("stats", {})
        ast_data = self.analysis_results.get("ast_data", {})
        deps_data = self.analysis_results.get("deps_data", {})
        components_data = self.analysis_results.get("components_data", {})

        summary_parts = [
            "**Statistics:**",
            f"- Modules: {stats.get('modules', 0)}",
            f"- Functions: {stats.get('functions', 0)}",
            f"- Classes: {stats.get('classes', 0)}",
        ]

        if ast_data:
            summary_parts.append("\n**Key Modules:**")
            for module in list(ast_data.keys())[:5]:
                summary_parts.append(f"- {module}")

        if components_data and "components" in components_data:
            summary_parts.append(
                f"\n**Components:** {len(components_data['components'])} identified"
            )

        if deps_data:
            external_deps = deps_data.get("external_dependencies", {})
            if external_deps:
                unique_deps: set = set()
                for deps_list in external_deps.values():
                    unique_deps.update(deps_list)
                summary_parts.append(
                    f"\n**External Dependencies:** {len(unique_deps)} packages"
                )

        return "\n".join(summary_parts)

    def _load_enriched_doc_artifacts(self) -> List[Dict[str, Any]]:
        """Load doc_artifacts.json from the artifacts directory."""
        import json

        artifact_path = self.artifacts_dir / "doc_artifacts.json"
        if not artifact_path.exists():
            return []
        try:
            data = json.loads(artifact_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []

        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for key in ("symbols", "entries", "functions"):
                val = data.get(key)
                if isinstance(val, list):
                    return val
        return []

    @staticmethod
    def _extract_components(components_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        if isinstance(components_data, list):
            return components_data
        if isinstance(components_data, dict):
            val = components_data.get("components") or []
            if isinstance(val, list):
                return val
        return []

    @staticmethod
    def _extract_external_deps(deps_data: Dict[str, Any]) -> List[str]:
        if not deps_data:
            return []
        external = deps_data.get("external_dependencies", {})
        if isinstance(external, dict):
            unique: set = set()
            for v in external.values():
                if isinstance(v, list):
                    unique.update(v)
            return sorted(unique)
        if isinstance(external, list):
            return sorted(set(external))
        return []
