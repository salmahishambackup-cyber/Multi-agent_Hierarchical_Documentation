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
        
        # Save README
        readme_path = self.repo_path / "README.md"
        readme_path.write_text(readme_content, encoding="utf-8")
        
        print(f"✅ README generated: {readme_path}")
        
        return {
            "readme_path": str(readme_path),
            "content": readme_content,
        }
    
    def _build_analysis_summary(self) -> str:
        """Build a summary of the analysis results."""
        stats = self.analysis_results.get("stats", {})
        ast_data = self.analysis_results.get("ast_data", {})
        deps_data = self.analysis_results.get("deps_data", {})
        components_data = self.analysis_results.get("components_data", {})
        
        summary_parts = []
        
        # Basic stats
        summary_parts.append(f"**Statistics:**")
        summary_parts.append(f"- Modules: {stats.get('modules', 0)}")
        summary_parts.append(f"- Functions: {stats.get('functions', 0)}")
        summary_parts.append(f"- Classes: {stats.get('classes', 0)}")
        
        # Key modules
        if ast_data:
            module_names = list(ast_data.keys())[:5]
            summary_parts.append(f"\n**Key Modules:**")
            for module in module_names:
                summary_parts.append(f"- {module}")
        
        # Components
        if components_data and "components" in components_data:
            summary_parts.append(f"\n**Components:** {len(components_data['components'])} identified")
        
        # Dependencies
        if deps_data:
            external_deps = deps_data.get("external_dependencies", {})
            if external_deps:
                # Count unique external dependencies
                unique_deps = set()
                for deps_list in external_deps.values():
                    unique_deps.update(deps_list)
                summary_parts.append(f"\n**External Dependencies:** {len(unique_deps)} packages")
        
        return "\n".join(summary_parts)
