#!/usr/bin/env python3
"""
Test script for the enhanced Phase 1 StructuralAgent.
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, '.')

# Import directly to avoid torch import issues
from agents.structural_agent import StructuralAgent

def test_structural_agent():
    """Test StructuralAgent on this repository."""
    repo_path = Path(".").resolve()
    artifacts_dir = Path("./test_artifacts_structural").resolve()
    
    print("Testing Enhanced Phase 1: StructuralAgent")
    print(f"Repository: {repo_path}")
    print(f"Artifacts: {artifacts_dir}")
    
    try:
        # Initialize and run agent
        agent = StructuralAgent(
            repo_path=str(repo_path),
            artifacts_dir=str(artifacts_dir),
            enable_performance_monitoring=True,
            enable_edge_case_detection=True,
            enable_validation=True,
        )
        
        results = agent.run()
        
        print("\n" + "="*60)
        print("✅ StructuralAgent Test Completed Successfully!")
        print("="*60)
        print(f"Modules: {results['stats']['modules']}")
        print(f"Functions: {results['stats']['functions']}")
        print(f"Classes: {results['stats']['classes']}")
        print(f"\nArtifacts saved to: {artifacts_dir}")
        print(f"  - AST: {results['ast_path']}")
        print(f"  - Dependencies: {results['deps_path']}")
        print(f"  - Components: {results['components_path']}")
        
        if results.get('edge_case_report'):
            print(f"\nEdge Cases:")
            report = results['edge_case_report']
            print(f"  - Circular imports: {len(report.get('circular_imports', []))}")
            print(f"  - Monolithic files: {len(report.get('monolithic_files', []))}")
            print(f"  - Generated files: {len(report.get('generated_files', []))}")
        
        return True
    except Exception as e:
        print(f"\n❌ StructuralAgent Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_structural_agent()
    sys.exit(0 if success else 1)
