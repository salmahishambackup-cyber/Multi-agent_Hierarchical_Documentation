"""Repository structure builder."""

from typing import Dict, Any, List
from pathlib import Path


def build_structure(ast_data: Dict[str, Any], deps_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build repository structure knowledge.
    
    Args:
        ast_data: AST information
        deps_data: Dependency information
        
    Returns:
        Repository structure dictionary
    """
    structure = {
        "files": {},
        "directories": {},
        "languages": {},
        "summary": {}
    }
    
    # Process files
    for file_path, file_info in ast_data.items():
        language = file_info.get("language", "unknown")
        
        # Add to files
        structure["files"][file_path] = {
            "language": language,
            "functions": len(file_info.get("functions", [])),
            "classes": len(file_info.get("classes", [])),
            "imports": len(file_info.get("imports", []))
        }
        
        # Track languages
        if language not in structure["languages"]:
            structure["languages"][language] = []
        structure["languages"][language].append(file_path)
        
        # Track directories
        dir_path = str(Path(file_path).parent)
        if dir_path not in structure["directories"]:
            structure["directories"][dir_path] = []
        structure["directories"][dir_path].append(file_path)
    
    # Build summary
    structure["summary"] = {
        "total_files": len(ast_data),
        "total_functions": sum(
            len(f.get("functions", [])) for f in ast_data.values()
        ),
        "total_classes": sum(
            len(f.get("classes", [])) for f in ast_data.values()
        ),
        "languages": list(structure["languages"].keys()),
        "directories": len(structure["directories"])
    }
    
    return structure
