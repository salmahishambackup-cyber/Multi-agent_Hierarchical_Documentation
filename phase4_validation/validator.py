"""
Phase 4: Validation and iterative improvement.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List, Tuple

from phase2_docstrings.agents import Writer
from phase4_validation.agents import Critic
from utils.profiler import profile_phase


class Validator:
    """
    Phase 4: Validate README sections and regenerate if needed.
    Uses heuristic validation first, LLM as fallback.
    """
    
    def __init__(
        self,
        writer: Writer,
        critic: Critic,
        repo_path: str,
        readme_content: str,
        max_retries: int = 2,
    ):
        """
        Initialize validator.
        
        Args:
            writer: Writer agent for regeneration
            critic: Critic for validation
            repo_path: Path to repository
            readme_content: README content to validate
            max_retries: Maximum retries per section
        """
        self.writer = writer
        self.critic = critic
        self.repo_path = Path(repo_path).resolve()
        self.readme_content = readme_content
        self.max_retries = max_retries
    
    @profile_phase("Phase 4: Validation")
    def run(self) -> Dict[str, Any]:
        """
        Validate README and regenerate failed sections.
        
        Returns:
            Dictionary with validation results and updated content
        """
        # Extract sections
        sections = self.critic.extract_readme_sections(self.readme_content)
        
        print(f"Validating {len(sections)} sections...")
        
        validation_results = {}
        regenerated = []
        
        # Required sections
        required_sections = ["title", "overview", "features", "architecture", "installation", "usage"]
        
        for section_name in required_sections:
            if section_name not in sections:
                validation_results[section_name] = {
                    "valid": False,
                    "issues": ["Section missing"],
                    "regenerated": False,
                }
                print(f"⚠️ {section_name}: Missing")
                continue
            
            section_content = sections[section_name]
            is_valid, issues = self.critic.validate_readme_section(section_name, section_content)
            
            if is_valid:
                validation_results[section_name] = {
                    "valid": True,
                    "issues": [],
                    "regenerated": False,
                }
                print(f"✅ {section_name}: Valid")
            else:
                # Try to regenerate
                print(f"⚠️ {section_name}: {', '.join(issues)}")
                
                # For now, just mark as invalid
                # In a full implementation, we would regenerate the specific section
                validation_results[section_name] = {
                    "valid": False,
                    "issues": issues,
                    "regenerated": False,
                }
        
        # Check if all sections are valid
        all_valid = all(result["valid"] for result in validation_results.values())
        
        if all_valid:
            print("✅ All sections valid")
        else:
            invalid_count = sum(1 for result in validation_results.values() if not result["valid"])
            print(f"⚠️ {invalid_count} sections need improvement")
        
        return {
            "all_valid": all_valid,
            "sections": validation_results,
            "regenerated": regenerated,
            "updated_content": self.readme_content,  # Would be updated if we regenerated
        }
