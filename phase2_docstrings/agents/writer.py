"""
Writer agent for generating documentation content.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional
from utils.llm_client import LLMClient


class Writer:
    """
    LLM-based writer for generating documentation content.
    """
    
    def __init__(self, llm_client: LLMClient):
        """
        Initialize writer with LLM client.
        
        Args:
            llm_client: LLM client instance
        """
        self.llm = llm_client
        # Get the repository root (go up from phase2_docstrings/agents/)
        self.repo_root = Path(__file__).parent.parent.parent
    
    def _load_prompt(self, name: str) -> str:
        """
        Load prompt template from file.
        
        Looks for prompts in phase-specific directories:
        - docstring: phase2_docstrings/prompts/
        - readme: phase3_readme/prompts/
        - evaluation: phase5_evaluation/prompts/
        """
        # Map prompt names to their phase locations
        prompt_locations = {
            "docstring": self.repo_root / "phase2_docstrings" / "prompts" / "docstring.md",
            "readme": self.repo_root / "phase3_readme" / "prompts" / "readme.md",
            "evaluation": self.repo_root / "phase5_evaluation" / "prompts" / "evaluation.md",
        }
        
        prompt_path = prompt_locations.get(name)
        if prompt_path and prompt_path.exists():
            return prompt_path.read_text()
        
        # Fallback to old agents/prompts location if phase-specific not found
        fallback_path = self.repo_root / "agents" / "prompts" / f"{name}.md"
        if fallback_path.exists():
            return fallback_path.read_text()
        
        raise FileNotFoundError(f"Prompt '{name}' not found in any expected location")
    
    def generate_docstring(self, code: str, context: str = "") -> str:
        """
        Generate Google-style docstring for code.
        
        Args:
            code: Code to document
            context: Additional context (imports, dependencies)
            
        Returns:
            Generated docstring
        """
        template = self._load_prompt("docstring")
        prompt = template.replace("{{code}}", code).replace("{{context}}", context)
        
        return self.llm.generate(
            prompt=prompt,
            max_new_tokens=400,
        )
    
    def generate_readme(self, project_name: str, analysis_summary: str) -> str:
        """
        Generate complete README with 6 sections.
        
        Args:
            project_name: Name of the project
            analysis_summary: Summary of code analysis
            
        Returns:
            Complete README content in markdown
        """
        template = self._load_prompt("readme")
        prompt = template.replace("{{project_name}}", project_name)
        prompt = prompt.replace("{{analysis_summary}}", analysis_summary)
        
        return self.llm.generate(
            prompt=prompt,
            max_new_tokens=1024,
            temperature=0.2,
        )
    
    def evaluate_documentation(self, readme_content: str) -> str:
        """
        Evaluate README documentation quality.
        
        Args:
            readme_content: README content to evaluate
            
        Returns:
            JSON string with evaluation results
        """
        template = self._load_prompt("evaluation")
        prompt = template.replace("{{readme_content}}", readme_content)
        
        return self.llm.generate(
            prompt=prompt,
            max_new_tokens=512,
            temperature=0.1,
        )
