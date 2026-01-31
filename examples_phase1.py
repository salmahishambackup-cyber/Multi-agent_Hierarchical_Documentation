#!/usr/bin/env python3
"""
Example: Using the Enhanced Phase 1 StructuralAgent

This script demonstrates how to use the enhanced Phase 1 implementation
with performance monitoring, edge case detection, and schema validation.
"""

import sys
from pathlib import Path

# NOTE: In the current test environment, there's a PyTorch import issue
# that prevents runtime execution. This script shows the intended usage.
# In a proper environment, uncomment the import and run() call below.

# from agents.structural_agent import StructuralAgent

def example_basic_usage():
    """Example: Basic usage of StructuralAgent."""
    print("="*60)
    print("Example 1: Basic Usage")
    print("="*60)
    
    # Uncomment in proper environment:
    # agent = StructuralAgent(
    #     repo_path=".",  # Current repository
    #     artifacts_dir="./artifacts"
    # )
    # results = agent.run()
    # 
    # print(f"✅ Analysis complete!")
    # print(f"Modules: {results['stats']['modules']}")
    # print(f"Functions: {results['stats']['functions']}")
    # print(f"Classes: {results['stats']['classes']}")
    
    print("""
    Code:
        agent = StructuralAgent(
            repo_path=".",
            artifacts_dir="./artifacts"
        )
        results = agent.run()
    
    Results:
        - modules: Number of source files analyzed
        - functions: Total functions found
        - classes: Total classes found
    """)

def example_with_monitoring():
    """Example: With performance monitoring."""
    print("\n" + "="*60)
    print("Example 2: With Performance Monitoring")
    print("="*60)
    
    # Uncomment in proper environment:
    # agent = StructuralAgent(
    #     repo_path=".",
    #     artifacts_dir="./artifacts",
    #     enable_performance_monitoring=True,  # Enable timing/memory tracking
    #     enable_edge_case_detection=True,     # Detect circular imports, etc.
    #     enable_validation=True               # Validate output schemas
    # )
    # results = agent.run()
    # 
    # # Access performance metrics
    # if results.get('performance_summary'):
    #     summary = results['performance_summary']
    #     print(f"Total duration: {summary['overall_duration_seconds']:.2f}s")
    #     for stage in summary['stages']:
    #         print(f"  - {stage['stage_name']}: {stage['duration_seconds']:.2f}s")
    
    print("""
    Code:
        agent = StructuralAgent(
            repo_path=".",
            enable_performance_monitoring=True,
            enable_edge_case_detection=True,
            enable_validation=True
        )
        results = agent.run()
        
        # Performance metrics available in results
        summary = results['performance_summary']
        
    Outputs:
        - Stage-by-stage timing
        - Memory usage deltas
        - Optimization suggestions
    """)

def example_edge_cases():
    """Example: Edge case detection."""
    print("\n" + "="*60)
    print("Example 3: Edge Case Detection")
    print("="*60)
    
    # Uncomment in proper environment:
    # agent = StructuralAgent(
    #     repo_path=".",
    #     artifacts_dir="./artifacts",
    #     enable_edge_case_detection=True
    # )
    # results = agent.run()
    # 
    # # Check for edge cases
    # if results.get('edge_case_report'):
    #     report = results['edge_case_report']
    #     
    #     if report['circular_imports']:
    #         print("⚠️  Circular imports detected:")
    #         for ci in report['circular_imports']:
    #             print(f"     {' -> '.join(ci['cycle'])}")
    #     
    #     if report['monolithic_files']:
    #         print("⚠️  Large files detected:")
    #         for mf in report['monolithic_files']:
    #             print(f"     {mf['file']}: {mf['lines_of_code']} LOC")
    #     
    #     if report['generated_files']:
    #         print("ℹ️  Generated files detected:")
    #         for gf in report['generated_files']:
    #             print(f"     {gf['file']}")
    
    print("""
    Code:
        agent = StructuralAgent(
            repo_path=".",
            enable_edge_case_detection=True
        )
        results = agent.run()
        
        report = results['edge_case_report']
        
    Edge Cases Detected:
        - Circular imports (cycles in dependency graph)
        - Monolithic files (>1000 LOC or >50 functions)
        - Generated code (auto-generated patterns)
    """)

def example_with_orchestrator():
    """Example: Using through Orchestrator."""
    print("\n" + "="*60)
    print("Example 4: Using Through Orchestrator")
    print("="*60)
    
    # Uncomment in proper environment:
    # from pipeline.orchestrator import Orchestrator
    # 
    # orchestrator = Orchestrator(
    #     repo_path=".",
    #     artifacts_dir="./artifacts",
    #     use_structural_agent=True  # Use enhanced agent (default)
    # )
    # 
    # # Run Phase 1
    # phase1_results = orchestrator.run_phase1()
    # 
    # # Continue with other phases
    # orchestrator.run_phase2()
    # orchestrator.run_phase3()
    # # ... etc
    
    print("""
    Code:
        from pipeline.orchestrator import Orchestrator
        
        orchestrator = Orchestrator(
            repo_path=".",
            use_structural_agent=True  # Default
        )
        
        phase1_results = orchestrator.run_phase1()
        
    Benefits:
        - Integrated with full pipeline
        - Backward compatible
        - Can switch between old/new with one parameter
    """)

def example_multi_language():
    """Example: Multi-language analysis."""
    print("\n" + "="*60)
    print("Example 5: Multi-Language Repository")
    print("="*60)
    
    print("""
    The agent automatically detects and analyzes:
    
    Supported Languages:
        ✓ Python (.py)
        ✓ Java (.java)
        ✓ JavaScript (.js, .jsx)
        ✓ TypeScript (.ts, .tsx)
        ✓ C (.c, .h)
        ✓ C++ (.cpp, .cc, .cxx, .hpp)
        ✓ C# (.cs)
    
    Features:
        - Cross-language dependency detection
        - Per-language standard library detection
        - Dynamic import pattern detection
        - Language-specific AST parsing
    
    Usage:
        agent = StructuralAgent(repo_path="./my-polyglot-project")
        results = agent.run()
        
        # Results include language breakdown
        for file_path, ast_info in results['ast_data'].items():
            print(f"{file_path}: {ast_info['language']}")
    """)

def main():
    """Run all examples."""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*10 + "Phase 1 StructuralAgent Examples" + " "*15 + "║")
    print("╚" + "="*58 + "╝")
    
    example_basic_usage()
    example_with_monitoring()
    example_edge_cases()
    example_with_orchestrator()
    example_multi_language()
    
    print("\n" + "="*60)
    print("📖 For more information, see PHASE1_UPGRADE.md")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
