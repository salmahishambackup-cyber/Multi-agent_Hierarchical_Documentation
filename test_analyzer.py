#!/usr/bin/env python3
"""
Test script to validate Phase 1 (analyzer) works without LLM.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, '.')

# Import only what we need for analyzer
from analyzer import extract_ast_info, build_dependency_graph, extract_components, detect_language
from utils.io_tools import write_json, ensure_dir
from pathlib import Path
from typing import List

def test_analyzer():
    """Test analyzer on this repository."""
    repo_path = Path(".").resolve()
    artifacts_dir = Path("./test_artifacts").resolve()
    
    print("Testing Phase 1: Analyzer")
    print(f"Repository: {repo_path}")
    print(f"Artifacts: {artifacts_dir}")
    
    ensure_dir(artifacts_dir)
    
    try:
        # Find Python files
        python_files = list(repo_path.rglob("*.py"))
        python_files = [f for f in python_files if "__pycache__" not in str(f) and "test_artifacts" not in str(f)][:5]  # Limit to 5 for testing
        
        print(f"\nProcessing {len(python_files)} files...")
        
        # Extract AST
        ast_data = {}
        for file_path in python_files:
            rel_path = file_path.relative_to(repo_path).as_posix()
            try:
                content = file_path.read_bytes()
                ast_info = extract_ast_info(str(file_path), content, str(repo_path))
                if ast_info:
                    ast_data[rel_path] = ast_info
            except Exception as e:
                print(f"Warning: Failed to parse {rel_path}: {e}")
        
        print(f"Parsed {len(ast_data)} files")
        
        # Build dependencies
        ast_list = list(ast_data.values())
        deps_data = build_dependency_graph(ast_list, str(repo_path))
        
        print(f"Found {len(deps_data.get('edges', []))} dependencies")
        
        # Extract components
        components_data = extract_components(ast_list, deps_data)
        print(f"Identified {len(components_data)} components")
        
        # Save artifacts
        write_json(artifacts_dir / "ast.json", ast_data)
        write_json(artifacts_dir / "dependencies.json", deps_data)
        write_json(artifacts_dir / "components.json", components_data)
        
        # Summary stats
        total_functions = sum(len(info.get("functions", [])) for info in ast_data.values())
        total_classes = sum(len(info.get("classes", [])) for info in ast_data.values())
        
        print("\n✅ Analyzer completed successfully!")
        print(f"Modules: {len(ast_data)}")
        print(f"Functions: {total_functions}")
        print(f"Classes: {total_classes}")
        
        return True
    except Exception as e:
        print(f"\n❌ Analyzer failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_analyzer()
    sys.exit(0 if success else 1)
