#!/usr/bin/env python3
"""
Minimal syntax check for Phase 1 integration.
Tests module imports without executing code.
"""

import sys
import ast

def check_syntax(filepath):
    """Check if a Python file has valid syntax."""
    try:
        with open(filepath, 'r') as f:
            code = f.read()
        ast.parse(code)
        return True, None
    except SyntaxError as e:
        return False, str(e)

def main():
    """Check syntax of all key files."""
    files_to_check = [
        'agents/structural_agent.py',
        'agents/base_agent.py',
        'pipeline/orchestrator.py',
        'utils/determinism.py',
        'utils/edge_case_handler.py',
        'utils/performance_metrics.py',
        'utils/schema_validator.py',
        'utils/file_filter.py',
        'utils/file_loader.py',
        'utils/json_writer.py',
        'utils/id_generator.py',
        'utils/path_utils.py',
        'utils/repo_scanner.py',
        'knowledge/structure_builder.py',
    ]
    
    print("Checking syntax of Phase 1 files...")
    all_pass = True
    
    for filepath in files_to_check:
        valid, error = check_syntax(filepath)
        if valid:
            print(f"✓ {filepath}")
        else:
            print(f"✗ {filepath}: {error}")
            all_pass = False
    
    if all_pass:
        print("\n✅ All files have valid syntax!")
        return 0
    else:
        print("\n❌ Some files have syntax errors")
        return 1

if __name__ == "__main__":
    sys.exit(main())
