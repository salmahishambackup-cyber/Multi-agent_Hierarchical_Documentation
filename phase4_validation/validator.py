"""
Phase 4: Validation and iterative improvement.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Any, List, Tuple

from phase2_docstrings.agents import Writer
from phase4_validation.agents import Critic
from utils.profiler import profile_phase


# Placeholder / weak-output patterns that indicate a low-quality generated README
_PLACEHOLDER_PATTERNS = [
    re.compile(r'\bupdated\b', re.IGNORECASE),
    re.compile(r'\bunknown\b', re.IGNORECASE),
    re.compile(r'\bfeature\s+\d+\b', re.IGNORECASE),     # "Feature 1", "Feature 2"
    re.compile(r'\bTODO\b'),
    re.compile(r'\bplaceholder\b', re.IGNORECASE),
    re.compile(r'\bsample\s+project\b', re.IGNORECASE),
    re.compile(r'\bmy[\s_-]?project\b', re.IGNORECASE),
]


def _detect_weak_patterns(content: str) -> List[str]:
    """
    Scan README content for placeholder or generic text that indicates
    a low-quality generated output.

    Args:
        content: Full README markdown content.

    Returns:
        List of human-readable issue descriptions. Empty list means no issues.
    """
    issues = []
    for pattern in _PLACEHOLDER_PATTERNS:
        matches = pattern.findall(content)
        if matches:
            unique_matches = list(dict.fromkeys(m.strip() for m in matches))[:3]
            issues.append(
                f"Placeholder/weak text detected: {unique_matches} "
                f"(pattern: {pattern.pattern!r})"
            )
    return issues


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
        Validate README and detect weak output patterns.

        Checks:
        - All required sections are present
        - Each section passes heuristic quality rules
        - No placeholder / weak-output patterns (e.g. "updated", "unknown",
          "Feature 1") appear in the document

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
                print(f"⚠️ {section_name}: {', '.join(issues)}")
                validation_results[section_name] = {
                    "valid": False,
                    "issues": issues,
                    "regenerated": False,
                }

        # --- Weak-output pattern detection (full document) ---
        weak_issues = _detect_weak_patterns(self.readme_content)
        if weak_issues:
            print(f"⚠️ Weak output patterns detected in README:")
            for issue in weak_issues:
                print(f"   • {issue}")
        else:
            print("✅ No weak output patterns detected")

        # Check if all sections are valid
        all_valid = (
            all(result["valid"] for result in validation_results.values())
            and len(weak_issues) == 0
        )
        
        if all_valid:
            print("✅ All sections valid")
        else:
            invalid_count = sum(1 for result in validation_results.values() if not result["valid"])
            print(
                f"⚠️ {invalid_count + len(weak_issues)} issue(s) found "
                f"(sections: {invalid_count}, weak patterns: {len(weak_issues)})"
            )
        
        return {
            "all_valid": all_valid,
            "sections": validation_results,
            "weak_pattern_issues": weak_issues,
            "regenerated": regenerated,
            "updated_content": self.readme_content,
        }
