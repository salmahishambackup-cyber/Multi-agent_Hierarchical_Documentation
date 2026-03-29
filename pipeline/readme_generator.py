"""
Phase 3 & Phase 8: README generation.

Phase 3 uses the Writer agent to produce a README with 6 sections.
Phase 8 (enhanced) generates a comprehensive README with all 11 required
sections using actual analysis data from the target project, not hardcoded
content about the documentation tool.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from agents import Writer
from utils import write_json
from utils.profiler import profile_phase


class ReadmeGenerator:
    """
    Generates README.md for the documented project.

    When *enhanced* is False (default), produces 6 sections via a single
    LLM call — compatible with the existing Phase 3 pipeline.

    When *enhanced* is True, produces all 11 required sections with rich
    content sourced from the enriched artifacts directory, documenting the
    *target project* rather than the documentation tool itself.
    """

    # Section order for the enhanced README
    _ENHANCED_SECTIONS: List[str] = [
        "Project Title & Metadata",
        "Executive Summary",
        "Business Context & Motivation",
        "System Architecture",
        "Functions & Business Logic",
        "Component & Module Reference",
        "Getting Started",
        "Usage Guide",
        "Developer Guide",
        "Deployment & Operations",
        "Troubleshooting & FAQs",
    ]

    # Validation constants
    _MIN_SECTION_LENGTH: int = 120
    _GENERIC_PHRASES: List[str] = [
        "this project",
        "the system",
        "various features",
        "many modules",
        "multiple components",
        "comprehensive solution",
    ]
    _SKIP_CODE_CHECK: set = {
        "Project Title & Metadata",
        "Troubleshooting & FAQs",
    }

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
        Generate README.md and, when enhanced, a .docs file.

        Returns:
            Dictionary with ``readme_path``, ``content``, and optionally
            ``docs_path`` keys.
        """
        if self.enhanced:
            readme_content = self._generate_enhanced()
        else:
            readme_content = self._generate_standard()

        readme_path = self.repo_path / "README.md"
        readme_path.write_text(readme_content, encoding="utf-8")

        result: Dict[str, Any] = {
            "readme_path": str(readme_path),
            "content": readme_content,
        }

        # Enhanced mode: also save a combined .docs file
        if self.enhanced:
            docs_path = self.artifacts_dir / f"{self.project_name}_documentation.docs"
            docs_path.write_text(readme_content, encoding="utf-8")
            result["docs_path"] = str(docs_path)
            print(f"📄 Combined .docs saved: {docs_path}")

        section_count = 11 if self.enhanced else 6
        print(f"✅ README generated ({section_count} sections): {readme_path}")

        return result

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
        Build a comprehensive README with all 11 required sections.

        Each section is processed sequentially through a four-step pipeline:
        GENERATE → VALIDATE → ENHANCE → CONFIRM before moving to the next.

        Sections are assembled from structured data (ast_data, enriched
        doc_artifacts, deps_data) so the output always documents the
        *target project*, not the documentation tool.
        """
        print(f"Generating enhanced README (11 sections) for '{self.project_name}'…")
        print("Pipeline: GENERATE → VALIDATE → ENHANCE → CONFIRM → NEXT SECTION\n")

        stats = self.analysis_results.get("stats", {})
        ast_data = self.analysis_results.get("ast_data", {}) or {}
        deps_data = self.analysis_results.get("deps_data", {}) or {}
        components_data = self.analysis_results.get("components_data", {}) or {}
        enriched = self._load_enriched_doc_artifacts()
        components = self._extract_components(components_data)
        external_deps = self._extract_external_deps(deps_data)

        # Build the analysis context once — every section gets access to it
        analysis_context = self._build_full_analysis_context(
            stats, ast_data, enriched, components, external_deps,
        )

        # Define the section generators in order
        section_generators = [
            ("Project Title & Metadata", lambda: self._section_title(stats)),
            ("Executive Summary", lambda: self._section_executive_summary(stats, ast_data, enriched)),
            ("Business Context & Motivation", lambda: self._section_business_context(enriched)),
            ("System Architecture", lambda: self._section_architecture(ast_data, components)),
            ("Functions & Business Logic", lambda: self._section_functions_business_logic(ast_data, enriched)),
            ("Component & Module Reference", lambda: self._section_component_reference(ast_data, components, enriched)),
            ("Getting Started", lambda: self._section_getting_started(external_deps)),
            ("Usage Guide", lambda: self._section_usage_guide(enriched, ast_data)),
            ("Developer Guide", lambda: self._section_developer_guide(ast_data)),
            ("Deployment & Operations", lambda: self._section_deployment(external_deps)),
            ("Troubleshooting & FAQs", lambda: self._section_troubleshooting(enriched)),
        ]

        # Prepare section output directory
        sections_dir = self.artifacts_dir / "doc_sections"
        sections_dir.mkdir(parents=True, exist_ok=True)

        final_sections: List[str] = []

        for idx, (section_name, generator_fn) in enumerate(section_generators, 1):
            print(f"━━━ Section {idx}/{len(section_generators)}: {section_name} ━━━")

            # 1. GENERATE — build the base structured section
            print(f"  ▶ GENERATE …")
            base_content = generator_fn()

            # 2. VALIDATE — check specificity (is this about the target project?)
            print(f"  ▶ VALIDATE …")
            is_specific, issues = self._validate_section_specificity(
                section_name, base_content,
            )
            if is_specific:
                print(f"    ✓ Content is specific to {self.project_name}")
            else:
                print(f"    ⚠ Specificity issues: {'; '.join(issues)}")

            # 3. ENHANCE — use LLM to expand with full codebase context
            print(f"  ▶ ENHANCE …")
            enhanced_content = self._enhance_section_with_llm(
                section_name, base_content, analysis_context, issues,
            )

            # 4. CONFIRM — save individual .docs file and report
            docs_file = self._save_section_to_docs(
                sections_dir, idx, section_name, enhanced_content,
            )
            print(f"  ✅ Section [{idx}] complete. Saving to .docs…")
            print(f"     → {docs_file}\n")

            final_sections.append(enhanced_content)

        return "\n\n".join(final_sections)

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
        enriched: List[Dict[str, Any]],
    ) -> str:
        modules = stats.get("modules", 0)
        functions = stats.get("functions", 0)
        classes = stats.get("classes", 0)

        # Collect short descriptions from enriched entries (unique, non-empty)
        short_descs = list(
            dict.fromkeys(
                e.get("short_description", "").strip()
                for e in enriched
                if e.get("short_description", "").strip()
            )
        )[:6]

        # Determine main language/framework hints from deps
        module_names = list(ast_data.keys())[:8]

        lines = [
            "## Executive Summary\n",
            f"**{self.project_name}** is a Python project comprising "
            f"{modules} module(s), {functions} function(s), and {classes} class(es).",
            "",
        ]

        if short_descs:
            lines.append(
                "**Key capabilities identified from code analysis:**"
            )
            for desc in short_descs:
                lines.append(f"- {desc}")
            lines.append("")

        if module_names:
            lines.append(
                f"The project is structured across {len(module_names)} analysed "
                "source file(s):"
            )
            for m in module_names:
                lines.append(f"- `{m}`")
            lines.append("")

        # Use LLM to produce a richer summary if data is available
        if enriched:
            llm_context = "; ".join(short_descs[:4]) if short_descs else ""
            if llm_context:
                prompt = (
                    f"Write a concise 2-sentence executive summary for a software project "
                    f"named '{self.project_name}' based on these function descriptions: "
                    f"{llm_context}. Do not mention any documentation tools."
                )
                llm_text = self._llm_generate(prompt, max_tokens=200)
                if llm_text:
                    lines += [llm_text, ""]

        return "\n".join(lines)

    def _section_business_context(self, enriched: List[Dict[str, Any]]) -> str:
        # Collect unique non-empty business context strings
        contexts = list(
            dict.fromkeys(
                e.get("business_context", "").strip()
                for e in enriched
                if e.get("business_context", "").strip()
            )
        )

        # Collect unique detailed descriptions as supplementary context
        detailed = list(
            dict.fromkeys(
                e.get("detailed_description", "").strip()
                for e in enriched
                if e.get("detailed_description", "").strip()
            )
        )[:5]

        lines = ["## Business Context & Motivation\n"]

        if contexts:
            lines.append(
                "The following business contexts were identified directly from "
                "the project's source code and docstrings:\n"
            )
            for ctx in contexts[:8]:
                lines.append(f"- {ctx}")
        else:
            lines.append(
                f"Business context for **{self.project_name}** is derived from "
                "the modules, functions, and classes identified during static analysis."
            )

        if detailed:
            lines += ["", "**Functional highlights:**"]
            for desc in detailed:
                lines.append(f"- {desc}")

        # Ask LLM to infer a business problem statement if we have any context
        if contexts or detailed:
            combined = ". ".join((contexts + detailed)[:5])
            prompt = (
                f"Based on these descriptions from the project '{self.project_name}': "
                f"{combined}\n\n"
                "Write 2 sentences explaining what business problem this project solves "
                "and who benefits from it. Be specific and avoid generic phrases."
            )
            llm_text = self._llm_generate(prompt, max_tokens=200)
            if llm_text:
                lines += ["", "**Problem & stakeholders:**", llm_text]

        return "\n".join(lines)

    def _section_architecture(
        self,
        ast_data: Dict[str, Any],
        components: List[Dict[str, Any]],
    ) -> str:
        lines = ["## System Architecture\n"]

        # Collect layers / roles from ast_data
        layer_map: Dict[str, List[str]] = {}
        for file_path, file_data in ast_data.items():
            if not isinstance(file_data, dict):
                continue
            layer = file_data.get("layer") or "general"
            layer_map.setdefault(layer, []).append(file_path)

        if layer_map:
            lines.append("### Module Layers\n")
            for layer, files in sorted(layer_map.items()):
                lines.append(f"**{layer.capitalize()}**")
                for f in files[:6]:
                    semantic_role = ""
                    fd = ast_data.get(f, {})
                    if isinstance(fd, dict):
                        semantic_role = fd.get("semantic_role") or ""
                    role_hint = f" — {semantic_role}" if semantic_role else ""
                    lines.append(f"- `{f}`{role_hint}")
                lines.append("")

        if components:
            lines.append("### Identified Components\n")
            for comp in components[:12]:
                name = comp.get("name") or comp.get("component_id") or "—"
                role = comp.get("business_role") or comp.get("type") or ""
                dep_list = comp.get("dependencies") or []
                dep_str = (
                    f" | deps: {', '.join(dep_list[:3])}" if dep_list else ""
                )
                lines.append(f"- **{name}**: {role}{dep_str}")
            lines.append("")

        if not layer_map and not components:
            files = list(ast_data.keys())
            if files:
                lines.append("### Source Modules\n")
                for f in files[:20]:
                    lines.append(f"- `{f}`")
            else:
                lines.append("_No architecture data available._")

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
            "\n".join(dep for dep in external_deps[:15])
            if external_deps
            else "# See requirements.txt or setup.py for dependencies"
        )

        # Check whether setup.py / pyproject.toml / requirements.txt exist
        install_hints: List[str] = []
        for candidate in ("requirements.txt", "setup.py", "pyproject.toml", "Pipfile"):
            if (self.repo_path / candidate).exists():
                install_hints.append(candidate)

        install_cmd = "pip install -r requirements.txt"
        if "pyproject.toml" in install_hints:
            install_cmd = "pip install ."
        elif "setup.py" in install_hints:
            install_cmd = "pip install -e ."

        return (
            "## Getting Started\n\n"
            "### Prerequisites\n\n"
            "- Python 3.8+\n"
            "- pip or conda\n\n"
            "### Installation\n\n"
            "```bash\n"
            "git clone <repository-url>\n"
            f"cd {self.project_name}\n"
            f"{install_cmd}\n"
            "```\n\n"
            "### Key dependencies\n\n"
            f"```text\n{deps_block}\n```"
        )

    def _section_functions_business_logic(
        self,
        ast_data: Dict[str, Any],
        enriched: List[Dict[str, Any]],
    ) -> str:
        """
        Build a detailed Functions & Business Logic section.

        Groups all enriched function/method/class entries by their source
        file, then renders full docstring information (signature, parameters,
        return type, business context, usage example) for each one.  Falls
        back to raw AST symbol names when enriched data is absent.
        """
        lines = ["## Functions & Business Logic\n"]
        lines.append(
            "This section documents all key functions, methods, and classes "
            f"identified in **{self.project_name}**, grouped by source file.\n"
        )

        # Build file → enriched entries lookup
        enriched_by_file: Dict[str, List[Dict[str, Any]]] = {}
        for entry in enriched:
            f = entry.get("file", "unknown")
            enriched_by_file.setdefault(f, []).append(entry)

        # Process each source file
        rendered_files: set = set()
        for file_path, file_data in ast_data.items():
            if not isinstance(file_data, dict):
                continue

            file_enriched = enriched_by_file.get(file_path, [])
            raw_functions = file_data.get("functions") or []
            raw_classes = file_data.get("classes") or []

            if not file_enriched and not raw_functions and not raw_classes:
                continue

            rendered_files.add(file_path)
            semantic_role = file_data.get("semantic_role") or ""
            role_hint = f" — *{semantic_role}*" if semantic_role else ""
            lines.append(f"### `{file_path}`{role_hint}\n")

            if file_enriched:
                for entry in file_enriched:
                    name = entry.get("name", "")
                    etype = entry.get("type", "function")
                    signature = entry.get("signature", "")
                    short_desc = entry.get("short_description", "")
                    detailed_desc = entry.get("detailed_description", "")
                    business_ctx = entry.get("business_context", "")
                    params = entry.get("parameters") or []
                    returns = entry.get("returns") or {}
                    example = entry.get("example", "")
                    side_effects = entry.get("side_effects") or []

                    if not name:
                        continue

                    # Heading: name with type badge
                    lines.append(f"#### `{name}` _{etype}_\n")

                    # Signature
                    if signature:
                        lines.append(f"```python\n{signature}\n```\n")

                    # Short description
                    if short_desc:
                        lines.append(f"**Summary:** {short_desc}\n")

                    # Detailed description
                    if detailed_desc:
                        lines.append(f"**Details:** {detailed_desc}\n")

                    # Business context
                    if business_ctx:
                        lines.append(f"**Business context:** {business_ctx}\n")

                    # Parameters table
                    if params:
                        lines.append("**Parameters:**\n")
                        lines.append("| Name | Type | Required | Description |")
                        lines.append("|------|------|----------|-------------|")
                        for p in params:
                            lines.append(self._render_param_row(p))
                        lines.append("")

                    # Return type
                    ret_rendered = self._render_returns(returns)
                    if ret_rendered:
                        lines.append(ret_rendered)

                    # Side effects
                    if side_effects:
                        effects_str = "; ".join(str(s) for s in side_effects[:4])
                        lines.append(f"**Side effects:** {effects_str}\n")

                    # Usage example
                    if example:
                        lines.append(f"**Example:**\n```python\n{example}\n```\n")

                    lines.append("")
            else:
                # Fallback: render raw symbol names from ast_data
                all_symbols = list(raw_functions) + list(raw_classes)
                for sym in all_symbols:
                    if not isinstance(sym, dict):
                        continue
                    sym_name = sym.get("name", "")
                    if sym_name:
                        lines.append(f"- `{sym_name}`")
                lines.append("")

        # Render enriched entries whose file wasn't in ast_data
        for file_path, entries in enriched_by_file.items():
            if file_path in rendered_files:
                continue
            lines.append(f"### `{file_path}`\n")
            for entry in entries:
                name = entry.get("name", "")
                etype = entry.get("type", "function")
                short_desc = entry.get("short_description", "")
                detailed_desc = entry.get("detailed_description", "")
                business_ctx = entry.get("business_context", "")
                signature = entry.get("signature", "")
                params = entry.get("parameters") or []
                returns = entry.get("returns") or {}
                example = entry.get("example", "")

                if not name:
                    continue

                lines.append(f"#### `{name}` _{etype}_\n")
                if signature:
                    lines.append(f"```python\n{signature}\n```\n")
                if short_desc:
                    lines.append(f"**Summary:** {short_desc}\n")
                if detailed_desc:
                    lines.append(f"**Details:** {detailed_desc}\n")
                if business_ctx:
                    lines.append(f"**Business context:** {business_ctx}\n")
                if params:
                    lines.append("**Parameters:**\n")
                    lines.append("| Name | Type | Required | Description |")
                    lines.append("|------|------|----------|-------------|")
                    for p in params:
                        lines.append(self._render_param_row(p))
                    lines.append("")
                ret_rendered = self._render_returns(returns)
                if ret_rendered:
                    lines.append(ret_rendered)
                if example:
                    lines.append(f"**Example:**\n```python\n{example}\n```\n")
                lines.append("")

        if len(lines) <= 2:
            lines.append("_No function data available from analysis._")

        return "\n".join(lines)

    def _section_usage_guide(
        self,
        enriched: List[Dict[str, Any]],
        ast_data: Dict[str, Any],
    ) -> str:
        lines = ["## Usage Guide\n"]

        # Find likely entry points: files named main.py, __main__.py,
        # or functions named main/run/start/execute at module level
        entry_points: List[Dict[str, Any]] = []
        for file_path, file_data in ast_data.items():
            if not isinstance(file_data, dict):
                continue
            basename = Path(file_path).name.lower()
            if basename in ("main.py", "__main__.py", "app.py", "run.py", "cli.py"):
                fns = file_data.get("functions") or []
                entry_points.append({"file": file_path, "functions": fns})

        if not entry_points:
            # Fall back: look for a main() function anywhere
            for file_path, file_data in ast_data.items():
                if not isinstance(file_data, dict):
                    continue
                fns = file_data.get("functions") or []
                for fn in fns:
                    if isinstance(fn, dict) and fn.get("name") in (
                        "main", "run", "start", "execute", "cli"
                    ):
                        entry_points.append({"file": file_path, "functions": [fn]})
                        break

        if entry_points:
            lines.append("### Entry Points\n")
            for ep in entry_points[:3]:
                lines.append(f"**`{ep['file']}`**")
                for fn in ep["functions"][:4]:
                    if isinstance(fn, dict):
                        fname = fn.get("name", "")
                        if fname:
                            lines.append(f"- `{fname}()`")
            lines.append("")

        # Examples from enriched doc_artifacts
        example_entries = [e for e in enriched if e.get("example")][:5]
        if example_entries:
            lines.append("### Code Examples\n")
            for entry in example_entries:
                name = entry.get("name", "")
                example = entry.get("example", "")
                short = entry.get("short_description", "")
                if short:
                    lines.append(f"**`{name}`** — {short}")
                else:
                    lines.append(f"**`{name}`:**")
                lines += [f"```python\n{example}\n```", ""]

        if not entry_points and not example_entries:
            lines.append(
                f"No explicit entry points were detected in **{self.project_name}**. "
                "Refer to the Functions & Business Logic section for the full public API."
            )

        return "\n".join(lines)

    def _section_developer_guide(self, ast_data: Dict[str, Any]) -> str:
        # Build actual folder tree from ast_data file paths
        tree_lines: List[str] = [f"{self.project_name}/"]
        dirs_seen: set = set()
        for file_path in sorted(ast_data.keys()):
            parts = Path(file_path).parts
            # Show directory entries
            for depth in range(len(parts) - 1):
                dir_path = "/".join(parts[: depth + 1])
                if dir_path not in dirs_seen:
                    dirs_seen.add(dir_path)
                    indent = "    " * depth
                    tree_lines.append(f"{indent}├── {parts[depth]}/")
            # File entry
            indent = "    " * (len(parts) - 1)
            tree_lines.append(f"{indent}├── {parts[-1]}")

        tree_str = "\n".join(tree_lines[:40])

        lines = [
            "## Developer Guide\n",
            "### Project Structure\n",
            "```",
            tree_str,
            "```\n",
            "### Testing\n",
            "```bash\n"
            "pytest tests/ -v\n"
            "```\n",
        ]

        return "\n".join(lines)

    def _section_deployment(self, external_deps: List[str]) -> str:
        dep_list = external_deps[:10]

        lines = [
            "## Deployment & Operations\n",
            "### Infrastructure\n",
            f"**{self.project_name}** runs as a Python application. "
            "No external services are required unless specified by the "
            "project's own configuration.\n",
        ]

        if dep_list:
            lines += [
                "### Runtime dependencies\n",
                "```text",
            ]
            lines += dep_list
            lines += ["```\n"]

        lines += [
            "### Running in production\n",
            "```bash\n"
            "# Install dependencies\n"
            "pip install -r requirements.txt\n\n"
            "# Run the application\n"
            f"python -m {self.project_name.replace('-', '_')}\n"
            "# or\n"
            "python main.py\n"
            "```\n",
        ]

        return "\n".join(lines)

    def _section_troubleshooting(self, enriched: List[Dict[str, Any]]) -> str:
        # Collect any raises documented in enriched entries
        known_exceptions: List[str] = []
        for entry in enriched:
            raises = entry.get("raises") or []
            for r in raises:
                if isinstance(r, dict):
                    exc = r.get("exception", "")
                    cond = r.get("condition", "")
                    if exc:
                        known_exceptions.append(
                            f"| `{exc}` | {cond} | Check the conditions described in the "
                            "Functions & Business Logic section |"
                        )

        lines = [
            "## Troubleshooting & FAQs\n",
            "### Common Issues\n",
        ]

        if known_exceptions:
            lines += [
                "The following exceptions are documented in the project source:\n",
                "| Exception | Condition | Resolution |",
                "|-----------|-----------|------------|",
            ]
            lines += list(dict.fromkeys(known_exceptions))[:10]
            lines.append("")

        lines += [
            "### General Tips\n",
            f"- Ensure all dependencies for **{self.project_name}** are installed "
            "(`pip install -r requirements.txt`).",
            "- Check Python version compatibility (3.8+ recommended).",
            "- Review function signatures and parameter types in the "
            "Functions & Business Logic section above.",
            "- Enable verbose/debug logging if the project provides that option.",
            "",
            "### Support\n",
            "Open an issue in the project repository with a description of the "
            "problem, the relevant error message, and steps to reproduce.",
        ]

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Section pipeline: GENERATE → VALIDATE → ENHANCE → CONFIRM
    # ------------------------------------------------------------------

    def _build_full_analysis_context(
        self,
        stats: Dict[str, Any],
        ast_data: Dict[str, Any],
        enriched: List[Dict[str, Any]],
        components: List[Dict[str, Any]],
        external_deps: List[str],
    ) -> str:
        """
        Build a comprehensive text summary of the target project.

        This context string is provided to every per-section LLM call so
        the model has full visibility into the codebase.
        """
        parts: List[str] = [
            f"Project: {self.project_name}",
            f"Modules: {stats.get('modules', 0)}, "
            f"Functions: {stats.get('functions', 0)}, "
            f"Classes: {stats.get('classes', 0)}",
        ]

        # Key modules with roles
        for fpath, fdata in list(ast_data.items())[:12]:
            if not isinstance(fdata, dict):
                continue
            role = fdata.get("semantic_role") or ""
            fns = fdata.get("functions") or []
            fn_names = ", ".join(
                f.get("name", "") for f in fns[:5] if isinstance(f, dict) and f.get("name")
            )
            entry = f"  Module `{fpath}`"
            if role:
                entry += f" ({role})"
            if fn_names:
                entry += f": {fn_names}"
            parts.append(entry)

        # Enriched summaries
        for e in enriched[:15]:
            name = e.get("name", "")
            short = e.get("short_description", "")
            bctx = e.get("business_context", "")
            if name and (short or bctx):
                parts.append(f"  • {name}: {short} {bctx}".strip())

        # Components
        for comp in components[:6]:
            cname = comp.get("name") or comp.get("component_id") or ""
            crole = comp.get("business_role") or comp.get("type") or ""
            if cname:
                parts.append(f"  Component '{cname}': {crole}")

        # External deps
        if external_deps:
            parts.append(f"  External deps: {', '.join(external_deps[:12])}")

        return "\n".join(parts)

    def _validate_section_specificity(
        self, section_name: str, content: str,
    ) -> tuple:
        """
        Check whether a generated section is specific to the target project.

        Returns:
            ``(is_specific, issues)`` — *issues* is a list of strings
            describing what is too generic.
        """
        issues: List[str] = []

        # 1. Content should reference the actual project name
        if self.project_name.lower() not in content.lower():
            issues.append(
                f"Does not mention the project name '{self.project_name}'"
            )

        # 2. Content should not be too short (except the title section)
        if section_name != "Project Title & Metadata" and len(content.strip()) < self._MIN_SECTION_LENGTH:
            issues.append("Content is very short — likely incomplete")

        # 3. Check for generic filler phrases
        lower = content.lower()
        for phrase in self._GENERIC_PHRASES:
            if phrase in lower:
                issues.append(f"Contains generic phrase: '{phrase}'")
                break  # one is enough to flag

        # 4. Should contain at least one back-ticked code reference
        if section_name not in self._SKIP_CODE_CHECK and "`" not in content:
            issues.append("No code references (back-ticked names) found")

        return len(issues) == 0, issues

    def _enhance_section_with_llm(
        self,
        section_name: str,
        base_content: str,
        analysis_context: str,
        validation_issues: List[str],
    ) -> str:
        """
        Use the LLM to expand and enrich a section with project-specific detail.

        The LLM receives the full analysis context so it can reference real
        module names, function signatures, and business logic.
        """
        # Title section doesn't need LLM enhancement
        if section_name == "Project Title & Metadata":
            return base_content

        issue_hint = ""
        if validation_issues:
            issue_hint = (
                "\n\nThe current draft has these specificity problems — "
                "fix them in your expanded version:\n- "
                + "\n- ".join(validation_issues)
            )

        prompt = (
            f"You are writing the '{section_name}' section of a technical "
            f"documentation file for a project named '{self.project_name}'.\n\n"
            f"=== FULL CODEBASE CONTEXT ===\n{analysis_context}\n"
            f"=== END CONTEXT ===\n\n"
            f"=== CURRENT DRAFT ===\n{base_content}\n=== END DRAFT ===\n"
            f"{issue_hint}\n\n"
            "INSTRUCTIONS:\n"
            "1. Expand this section with detailed, project-specific content.\n"
            "2. Reference REAL function names, module paths, class names, "
            "and parameters from the codebase context above.\n"
            "3. Tie every technical detail to a business outcome — explain "
            "WHY each piece exists, not just WHAT it does.\n"
            "4. Use Markdown headings (##, ###), tables, and ```python code "
            "snippets where appropriate.\n"
            "5. Do NOT include generic filler. Every sentence must be "
            f"specific to the '{self.project_name}' project.\n"
            "6. Keep the existing structure but make it substantially richer.\n\n"
            "Return ONLY the expanded Markdown section content."
        )

        enhanced = self._llm_generate(prompt, max_tokens=1024)

        # If LLM produced useful output, merge it; otherwise keep base
        if enhanced and len(enhanced.strip()) > len(base_content.strip()) // 2:
            # Prepend any structural header that the LLM may have dropped
            first_line = base_content.split("\n", 1)[0]
            if first_line.startswith("#") and not enhanced.lstrip().startswith("#"):
                enhanced = first_line + "\n\n" + enhanced
            return enhanced

        return base_content

    def _save_section_to_docs(
        self,
        sections_dir: Path,
        section_num: int,
        section_name: str,
        content: str,
    ) -> Path:
        """
        Save a single section as a ``.docs`` file in *sections_dir*.

        Returns the path to the saved file.
        """
        safe_name = section_name.lower().replace(" ", "_").replace("&", "and")
        filename = f"section_{section_num:02d}_{safe_name}.docs"
        path = sections_dir / filename
        path.write_text(content, encoding="utf-8")
        return path

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _render_param_row(p: Any) -> str:
        """Render a single parameter as a Markdown table row."""
        if not isinstance(p, dict):
            return "| — | Any | ✓ |  |"
        pname = p.get("name", "")
        ptype = p.get("type", "Any")
        preq = "✓" if p.get("required", True) else "✗"
        pdesc = p.get("description", "")
        return f"| `{pname}` | `{ptype}` | {preq} | {pdesc} |"

    @staticmethod
    def _render_returns(returns: Any) -> str:
        """Render a returns dict as a Markdown string, or '' if empty."""
        if not isinstance(returns, dict):
            return ""
        ret_type = returns.get("type", "")
        ret_desc = returns.get("description", "")
        if not ret_type and not ret_desc:
            return ""
        ret_str = f"`{ret_type}`" if ret_type else ""
        if ret_desc:
            ret_str = f"{ret_str} — {ret_desc}" if ret_str else ret_desc
        return f"**Returns:** {ret_str}\n"

    def _llm_generate(self, prompt: str, max_tokens: int = 1024) -> str:
        """
        Generate text via the Writer's underlying LLM.

        Returns an empty string on any error so callers can safely ignore
        the result when the LLM is unavailable.
        """
        try:
            return self.writer.llm.generate(
                prompt=prompt,
                max_new_tokens=max_tokens,
                temperature=0.2,
            )
        except Exception:
            return ""

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
