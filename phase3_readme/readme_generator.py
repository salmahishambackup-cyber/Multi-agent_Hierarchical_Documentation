"""
Phase 3: README generation with 6 required sections.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any

from phase2_docstrings.agents import Writer
from utils import write_json
from utils.profiler import profile_phase


class ReadmeGenerator:
    """
    Phase 3: Generate README.md with exactly 6 sections.
    Optimized to generate all sections in one LLM call.
    """
    
    def __init__(
        self,
        writer: Writer,
        repo_path: str,
        artifacts_dir: str,
        project_name: str,
        analysis_results: Dict[str, Any],
    ):
        """
        Initialize README generator.
        
        Args:
            writer: Writer agent for LLM generation
            repo_path: Path to repository
            artifacts_dir: Directory for artifacts
            project_name: Name of the project
            analysis_results: Results from Phase 1 analysis
        """
        self.writer = writer
        self.repo_path = Path(repo_path).resolve()
        self.artifacts_dir = Path(artifacts_dir).resolve()
        self.project_name = project_name
        self.analysis_results = analysis_results
    
    @profile_phase("Phase 3: README")
    def run(self) -> Dict[str, Any]:
        """
        Generate README with 6 sections.
        
        Returns:
            Dictionary with README path and content
        """
        # Build analysis summary
        analysis_summary = self._build_analysis_summary()
        
        # Generate complete README in one call
        print("Generating README (6 sections)...")
        readme_content = self.writer.generate_readme(
            project_name=self.project_name,
            analysis_summary=analysis_summary,
        )
        
        # Post-process: strip markdown code blocks if LLM wrapped the output
        readme_content = self._strip_code_blocks(readme_content)
        
        # Save README
        readme_path = self.repo_path / "README.md"
        readme_path.write_text(readme_content, encoding="utf-8")
        
        print(f"✅ README generated: {readme_path}")
        
        return {
            "readme_path": str(readme_path),
            "content": readme_content,
        }
    
    def _build_analysis_summary(self) -> str:
        """Build a rich summary of the analysis results including actual code elements."""
        stats = self.analysis_results.get("stats", {})
        ast_data = self.analysis_results.get("ast_data", {})
        deps_data = self.analysis_results.get("deps_data", {})
        components_data = self.analysis_results.get("components_data", {})

        summary_parts = []

        # Basic stats
        summary_parts.append("**Statistics:**")
        summary_parts.append(f"- Modules: {stats.get('modules', 0)}")
        summary_parts.append(f"- Functions: {stats.get('functions', 0)}")
        summary_parts.append(f"- Classes: {stats.get('classes', 0)}")

        # Key modules with docstrings / first-line descriptions
        if ast_data:
            module_names = list(ast_data.keys())
            summary_parts.append("\n**Key Modules:**")
            for module in module_names[:8]:
                module_info = ast_data[module]
                # Include existing module-level docstring if available
                existing_doc = (
                    module_info.get("module_docstring")
                    or module_info.get("docstring")
                    or ""
                )
                first_line = existing_doc.strip().split("\n")[0].strip() if existing_doc else ""
                if first_line:
                    summary_parts.append(f"- `{module}`: {first_line}")
                else:
                    summary_parts.append(f"- `{module}`")

        # Actual function and class names per module for feature generation
        if ast_data:
            summary_parts.append("\n**Key Functions & Classes (from AST):**")
            seen_names: set = set()
            for module, module_info in ast_data.items():
                for func in module_info.get("functions", [])[:5]:
                    fname = func.get("name", "")
                    if fname and fname not in seen_names:
                        seen_names.add(fname)
                        doc_first = ""
                        existing = func.get("docstring", "")
                        if existing:
                            doc_first = existing.strip().split("\n")[0].strip()
                        if doc_first:
                            summary_parts.append(f"- `{fname}()` ({module}): {doc_first}")
                        else:
                            summary_parts.append(f"- `{fname}()` ({module})")
                for cls in module_info.get("classes", [])[:3]:
                    cname = cls.get("name", "")
                    if cname and cname not in seen_names:
                        seen_names.add(cname)
                        summary_parts.append(f"- class `{cname}` ({module})")

        # File structure (first level)
        summary_parts.append("\n**File Structure:**")
        for module in list(ast_data.keys())[:10]:
            summary_parts.append(f"- `{module}`")

        # Components
        if components_data and "components" in components_data:
            comps = components_data["components"]
            summary_parts.append(f"\n**Components:** {len(comps)} identified")
            for comp in comps[:5]:
                comp_name = comp.get("name") or comp.get("component_id") or "unnamed"
                hypothesis = comp.get("hypothesis", "")
                if hypothesis:
                    summary_parts.append(f"- {comp_name}: {hypothesis}")
                else:
                    summary_parts.append(f"- {comp_name}")

        # External dependencies
        if deps_data:
            external_deps = deps_data.get("external_dependencies", {})
            if external_deps:
                unique_deps: set = set()
                for deps_list in external_deps.values():
                    unique_deps.update(deps_list)
                summary_parts.append(
                    f"\n**External Dependencies:** {', '.join(sorted(unique_deps)[:10])}"
                )

        return "\n".join(summary_parts)
    
    def _strip_code_blocks(self, content: str) -> str:
        """
        Strip markdown code blocks if LLM wrapped the output.
        
        Args:
            content: Generated content that might be wrapped in ```markdown```
            
        Returns:
            Clean content without code block wrappers
        """
        content = content.strip()
        
        # Check if content starts with ```markdown or ``` and ends with ```
        if content.startswith("```markdown"):
            # Remove opening ```markdown
            content = content[len("```markdown"):].lstrip()
        elif content.startswith("```"):
            # Remove opening ```
            content = content[3:].lstrip()
        
        if content.endswith("```"):
            # Remove closing ```
            content = content[:-3].rstrip()
        
        return content.strip()
