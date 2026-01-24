"""
Critic agent for lightweight quality review.
"""

from __future__ import annotations

import re
from typing import Dict, List, Tuple


class Critic:
    """
    Lightweight heuristic-based quality checker.
    Uses regex and simple rules before expensive LLM validation.
    """
    
    @staticmethod
    def validate_docstring(docstring: str) -> Tuple[bool, List[str]]:
        """
        Validate docstring quality using heuristics.
        
        Args:
            docstring: Docstring to validate
            
        Returns:
            Tuple of (is_valid, list of issues)
        """
        issues = []
        
        # Check minimum length
        if len(docstring.strip()) < 20:
            issues.append("Docstring too short (< 20 chars)")
        
        # Check for summary line
        lines = docstring.strip().split("\n")
        if not lines[0].strip():
            issues.append("Missing summary line")
        
        # Check for common sections (for functions)
        has_args = "Args:" in docstring or "Arguments:" in docstring or "Parameters:" in docstring
        has_returns = "Returns:" in docstring or "Return:" in docstring
        
        # If docstring mentions parameters in text, it should have Args section
        if re.search(r'\b(parameter|argument|param)\b', docstring, re.IGNORECASE):
            if not has_args:
                issues.append("Mentions parameters but missing Args section")
        
        return len(issues) == 0, issues
    
    @staticmethod
    def validate_readme_section(section_name: str, content: str) -> Tuple[bool, List[str]]:
        """
        Validate README section using heuristics.
        
        Args:
            section_name: Name of the section
            content: Section content
            
        Returns:
            Tuple of (is_valid, list of issues)
        """
        issues = []
        content_lower = content.lower()
        
        if section_name == "title":
            if len(content.strip()) < 3:
                issues.append("Title too short")
            if not content.strip().startswith("#"):
                issues.append("Title should start with #")
        
        elif section_name == "overview":
            sentences = content.split(".")
            if len(sentences) < 2:
                issues.append("Overview should have at least 2 sentences")
            if len(content.strip()) < 50:
                issues.append("Overview too short (< 50 chars)")
        
        elif section_name == "features":
            # Check for bullet points
            bullet_count = content.count("-") + content.count("*") + content.count("•")
            if bullet_count < 3:
                issues.append("Should have at least 3 bullet points")
        
        elif section_name == "architecture":
            # Check for directory tree or structure
            has_tree = "├" in content or "│" in content or "└" in content
            has_structure = "```" in content or "|" in content
            if not (has_tree or has_structure):
                issues.append("Should include directory tree or structure diagram")
        
        elif section_name == "installation":
            # Check for code block
            if "```" not in content:
                issues.append("Should include code block with commands")
            # Check for common installation keywords
            has_install = any(kw in content_lower for kw in ["pip", "install", "npm", "git clone", "requirements"])
            if not has_install:
                issues.append("Missing installation instructions")
        
        elif section_name == "usage":
            # Check for code example
            if "```" not in content:
                issues.append("Should include at least 1 code example")
            if len(content.strip()) < 50:
                issues.append("Usage section too short")
        
        return len(issues) == 0, issues
    
    @staticmethod
    def extract_readme_sections(readme_content: str) -> Dict[str, str]:
        """
        Extract sections from README content.
        
        Args:
            readme_content: Complete README content
            
        Returns:
            Dictionary mapping section names to content
        """
        sections = {}
        current_section = None
        current_content = []
        
        for line in readme_content.split("\n"):
            # Check if this is a header
            if line.startswith("#"):
                # Save previous section
                if current_section:
                    sections[current_section] = "\n".join(current_content).strip()
                
                # Start new section
                header_text = line.lstrip("#").strip().lower()
                
                # Normalize section names
                if "overview" in header_text or "description" in header_text:
                    current_section = "overview"
                elif "feature" in header_text:
                    current_section = "features"
                elif "architecture" in header_text or "structure" in header_text:
                    current_section = "architecture"
                elif "install" in header_text or "setup" in header_text:
                    current_section = "installation"
                elif "usage" in header_text or "example" in header_text:
                    current_section = "usage"
                elif len(sections) == 0:  # First header is title
                    current_section = "title"
                else:
                    current_section = header_text
                
                current_content = [line]
            else:
                current_content.append(line)
        
        # Save last section
        if current_section:
            sections[current_section] = "\n".join(current_content).strip()
        
        return sections
