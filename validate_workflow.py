#!/usr/bin/env python3
"""
Comprehensive workflow validation script.
Tests all phases to ensure proper functionality.
"""

import sys
from pathlib import Path

def test_imports():
    """Test that all imports work correctly."""
    print("=" * 70)
    print("TEST 1: Import Validation")
    print("=" * 70)
    
    try:
        print("✓ Importing Orchestrator...")
        from orchestrator import Orchestrator
        
        print("✓ Importing Phase 1 components...")
        from phase1_analysis import Analyzer, StructuralAgent
        
        print("✓ Importing Phase 2 components...")
        from phase2_docstrings import DocstringGenerator, Writer
        
        print("✓ Importing Phase 3 components...")
        from phase3_readme import ReadmeGenerator
        
        print("✓ Importing Phase 4 components...")
        from phase4_validation import Validator, Critic
        
        print("✓ Importing Phase 5 components...")
        from phase5_evaluation import Evaluator
        
        print("\n✅ All imports successful!\n")
        return True
    except Exception as e:
        print(f"\n❌ Import failed: {e}\n")
        return False


def test_prompt_locations():
    """Test that all prompt files exist and are accessible."""
    print("=" * 70)
    print("TEST 2: Prompt File Validation")
    print("=" * 70)
    
    repo_root = Path(__file__).parent
    
    prompts_to_check = [
        ("phase2_docstrings/prompts/docstring.md", "Docstring prompt"),
        ("phase3_readme/prompts/readme.md", "README prompt"),
        ("phase5_evaluation/prompts/evaluation.md", "Evaluation prompt"),
        ("agents/prompts/docstring.md", "Legacy docstring prompt"),
        ("agents/prompts/readme.md", "Legacy readme prompt"),
        ("agents/prompts/evaluation.md", "Legacy evaluation prompt"),
    ]
    
    all_exist = True
    for path, description in prompts_to_check:
        full_path = repo_root / path
        if full_path.exists():
            size = len(full_path.read_text())
            print(f"✓ {description:30s} [{path}] ({size} chars)")
        else:
            print(f"✗ {description:30s} [{path}] NOT FOUND")
            all_exist = False
    
    if all_exist:
        print("\n✅ All prompt files exist!\n")
    else:
        print("\n❌ Some prompt files missing!\n")
    
    return all_exist


def test_writer_prompt_loading():
    """Test that Writer can load prompts correctly."""
    print("=" * 70)
    print("TEST 3: Writer Prompt Loading")
    print("=" * 70)
    
    try:
        # Import Writer from phase2 location
        from phase2_docstrings.agents.writer import Writer
        from utils.llm_client import LLMClient
        
        # Create a dummy LLM client (we won't actually use it)
        class DummyLLM:
            def generate(self, prompt, **kwargs):
                return "dummy response"
        
        writer = Writer(DummyLLM())
        
        # Test loading each prompt type
        prompts = ["docstring", "readme", "evaluation"]
        for prompt_name in prompts:
            try:
                content = writer._load_prompt(prompt_name)
                print(f"✓ Loaded '{prompt_name}' prompt ({len(content)} chars)")
            except Exception as e:
                print(f"✗ Failed to load '{prompt_name}': {e}")
                return False
        
        print("\n✅ Writer can load all prompts!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Writer test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_writer_from_agents():
    """Test that legacy Writer can also load prompts correctly."""
    print("=" * 70)
    print("TEST 4: Legacy Writer Prompt Loading")
    print("=" * 70)
    
    try:
        # Import Writer from agents location
        from agents.writer import Writer
        
        # Create a dummy LLM client
        class DummyLLM:
            def generate(self, prompt, **kwargs):
                return "dummy response"
        
        writer = Writer(DummyLLM())
        
        # Test loading each prompt type
        prompts = ["docstring", "readme", "evaluation"]
        for prompt_name in prompts:
            try:
                content = writer._load_prompt(prompt_name)
                print(f"✓ Loaded '{prompt_name}' prompt ({len(content)} chars)")
            except Exception as e:
                print(f"✗ Failed to load '{prompt_name}': {e}")
                return False
        
        print("\n✅ Legacy Writer can load all prompts!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Legacy Writer test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_phase_structure():
    """Test that phase directories have correct structure."""
    print("=" * 70)
    print("TEST 5: Phase Directory Structure")
    print("=" * 70)
    
    repo_root = Path(__file__).parent
    
    phases = [
        ("phase1_analysis", ["agents", "analyzer", "__init__.py"]),
        ("phase2_docstrings", ["agents", "prompts", "__init__.py"]),
        ("phase3_readme", ["prompts", "__init__.py"]),
        ("phase4_validation", ["agents", "__init__.py"]),
        ("phase5_evaluation", ["prompts", "__init__.py"]),
    ]
    
    all_good = True
    for phase_dir, required_items in phases:
        phase_path = repo_root / phase_dir
        print(f"\nChecking {phase_dir}:")
        if not phase_path.exists():
            print(f"  ✗ Directory doesn't exist!")
            all_good = False
            continue
        
        for item in required_items:
            item_path = phase_path / item
            if item_path.exists():
                print(f"  ✓ {item}")
            else:
                print(f"  ✗ {item} NOT FOUND")
                all_good = False
    
    if all_good:
        print("\n✅ All phase structures correct!\n")
    else:
        print("\n❌ Some phase structures incomplete!\n")
    
    return all_good


def clear_cache_instructions():
    """Print instructions to clear Python cache."""
    print("=" * 70)
    print("CACHE CLEARING INSTRUCTIONS")
    print("=" * 70)
    print("""
If you're still seeing prompt loading errors, you need to clear Python's cache:

Method 1: Clear all .pyc files (recommended)
    $ find . -type f -name '*.pyc' -delete
    $ find . -type d -name '__pycache__' -exec rm -rf {} +

Method 2: In Colab/Jupyter, restart the runtime
    Runtime → Restart Runtime

Method 3: Force reload modules in Python
    import importlib
    import sys
    
    # Remove cached modules
    modules_to_clear = [k for k in sys.modules.keys() if 'phase' in k or 'writer' in k]
    for mod in modules_to_clear:
        del sys.modules[mod]

Then re-import and run again.
""")


def main():
    """Run all validation tests."""
    print("\n" + "=" * 70)
    print(" " * 15 + "WORKFLOW VALIDATION SUITE")
    print("=" * 70 + "\n")
    
    results = []
    
    # Run all tests
    results.append(("Imports", test_imports()))
    results.append(("Prompt Files", test_prompt_locations()))
    results.append(("Writer Loading", test_writer_prompt_loading()))
    results.append(("Legacy Writer", test_writer_from_agents()))
    results.append(("Phase Structure", test_phase_structure()))
    
    # Print summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:20s} {status}")
    
    all_passed = all(passed for _, passed in results)
    
    if all_passed:
        print("\n" + "🎉" * 35)
        print("\n✅ ALL TESTS PASSED! Workflow is ready to use.\n")
        print("🎉" * 35 + "\n")
        return 0
    else:
        print("\n" + "⚠️ " * 35)
        print("\n❌ SOME TESTS FAILED!")
        print("\nIf you see 'FileNotFoundError' errors:")
        clear_cache_instructions()
        print("⚠️ " * 35 + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
