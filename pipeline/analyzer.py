"""
Phase 1: Static code analysis using tree-sitter (no LLM).
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List
import json

from analyzer import (
    extract_ast_info,
    build_dependency_graph,
    extract_components,
    detect_language,
    compute_file_metrics,
)
from utils import write_json, ensure_dir
from utils.profiler import profile_phase


class Analyzer:
    """
    Phase 1: Project analysis using tree-sitter.
    Generates ast.json, dependencies_normalized.json, components.json.
    """
    
    def __init__(self, repo_path: str, artifacts_dir: str):
        """
        Initialize analyzer.
        
        Args:
            repo_path: Path to repository to analyze
            artifacts_dir: Directory to save artifacts
        """
        self.repo_path = Path(repo_path).resolve()
        self.artifacts_dir = Path(artifacts_dir).resolve()
        ensure_dir(self.artifacts_dir)
    
    @profile_phase("Phase 1: Analysis")
    def run(self) -> Dict[str, Any]:
        """
        Run static analysis on repository.
        
        Returns:
            Dictionary with paths to generated artifacts and summary stats
        """
        # Find all Python files
        python_files = self._find_python_files()
        
        print(f"Found {len(python_files)} Python files")
        
        # Extract AST info for each file
        ast_data = {}
        all_modules = []
        
        for file_path in python_files:
            rel_path = file_path.relative_to(self.repo_path).as_posix()
            
            try:
                content = file_path.read_bytes()
                ast_info = extract_ast_info(str(file_path), content, str(self.repo_path))
                
                if ast_info:
                    # Enrich with file metrics
                    language = ast_info.get("language", "python")
                    metrics = compute_file_metrics(ast_info, content, language)
                    ast_info["metrics"] = metrics
                    ast_data[rel_path] = ast_info
                    all_modules.append(rel_path)
            except Exception as e:
                # Safety-net: try stdlib ast fallback directly
                try:
                    from analyzer.ast_extractor import _extract_python_ast_fallback
                    fallback_result = _extract_python_ast_fallback(content, rel_path)
                    if fallback_result:
                        ast_data[rel_path] = fallback_result
                        all_modules.append(rel_path)
                        continue
                except Exception as fallback_err:
                    print(f"Warning: stdlib fallback also failed for {rel_path}: {fallback_err}")
                print(f"Warning: Failed to parse {rel_path}: {e}")
        
        # Save AST artifact
        ast_path = self.artifacts_dir / "ast.json"
        write_json(ast_path, ast_data)
        
        # Build dependency graph (convert dict to list)
        ast_list = list(ast_data.values())
        raw_deps_data = build_dependency_graph(ast_list, str(self.repo_path))
        
        # Transform to expected format
        deps_data = self._transform_dependencies(raw_deps_data)
        deps_path = self.artifacts_dir / "dependencies_normalized.json"
        write_json(deps_path, deps_data)
        
        # Extract components (also needs list)
        components_data = extract_components(ast_list, raw_deps_data)
        components_path = self.artifacts_dir / "components.json"
        write_json(components_path, components_data)
        
        # Summary stats
        total_functions = sum(
            len(info.get("functions", [])) for info in ast_data.values()
        )
        total_classes = sum(
            len(info.get("classes", [])) for info in ast_data.values()
        )
        
        print(f"✅ {len(all_modules)} modules, {total_functions} functions, {total_classes} classes")
        
        return {
            "ast_path": str(ast_path),
            "deps_path": str(deps_path),
            "components_path": str(components_path),
            "stats": {
                "modules": len(all_modules),
                "functions": total_functions,
                "classes": total_classes,
            },
            "ast_data": ast_data,
            "deps_data": deps_data,
            "components_data": components_data,
        }
    
    def _find_python_files(self) -> List[Path]:
        """Find all Python files in repository."""
        files = []
        
        # Common patterns to exclude
        exclude_patterns = [
            "__pycache__",
            ".git",
            ".venv",
            "venv",
            "env",
            "build",
            "dist",
            ".eggs",
            "*.egg-info",
        ]
        
        for py_file in self.repo_path.rglob("*.py"):
            # Check if file should be excluded
            should_exclude = any(
                pattern in str(py_file) for pattern in exclude_patterns
            )
            
            if not should_exclude:
                files.append(py_file)
        
        return files
    
    def _transform_dependencies(self, raw_deps: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform dependency graph format to expected format.
        
        Args:
            raw_deps: {"nodes": [...], "edges": [...]}
            
        Returns:
            {"internal_dependencies": {...}, "external_dependencies": {...}}
        """
        from collections import defaultdict
        
        internal_deps = defaultdict(list)
        external_deps = defaultdict(list)
        
        for edge in raw_deps.get("edges", []):
            from_file = edge.get("from")
            to_file = edge.get("to")
            kind = edge.get("kind", "")
            
            if not from_file or not to_file:
                continue
            
            # Check if it's an internal or external dependency
            if kind in ["internal", "cross_language"]:
                internal_deps[from_file].append(to_file)
            elif kind in ["external", "runtime"]:
                # Extract module name from external dependencies
                if to_file.startswith("external:"):
                    module = to_file.replace("external:", "")
                    external_deps[from_file].append(module)
                else:
                    external_deps[from_file].append(to_file)
        
        return {
            "internal_dependencies": dict(internal_deps),
            "external_dependencies": dict(external_deps),
            "raw_graph": raw_deps,  # Keep original for reference
        }
