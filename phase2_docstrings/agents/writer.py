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
        self.prompts_dir = Path(__file__).parent / "prompts"
    
    def _load_prompt(self, name: str) -> str:
        """Load prompt template from file."""
        return (self.prompts_dir / f"{name}.md").read_text()
    
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
