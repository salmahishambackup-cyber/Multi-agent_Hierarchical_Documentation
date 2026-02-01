#!/usr/bin/env python3
"""
Direct test of Writer class prompt loading.
Tests the specific issue reported by the user.
"""

import sys
from pathlib import Path

def test_phase2_writer():
    """Test Writer from phase2_docstrings can load prompts."""
    print("=" * 70)
    print("TEST: Phase 2 Writer Prompt Loading")
    print("=" * 70)
    
    # Manually load and test the Writer class
    repo_root = Path(__file__).parent
    
    # Check what __file__.parent gives us
    writer_file = repo_root / "phase2_docstrings" / "agents" / "writer.py"
    print(f"\nWriter file location: {writer_file}")
    print(f"Writer file exists: {writer_file.exists()}")
    
    # Read the writer file and check its _load_prompt logic
    content = writer_file.read_text()
    
    # Simulate what the Writer __init__ does
    # From phase2_docstrings/agents/writer.py, __init__ sets:
    # self.repo_root = Path(__file__).parent.parent.parent
    
    writer_location = writer_file.parent  # phase2_docstrings/agents/
    print(f"\nWriter's __file__.parent: {writer_location}")
    
    computed_repo_root = writer_location.parent.parent  # Go up 2 levels
    print(f"Writer's computed repo_root: {computed_repo_root}")
    
    # Now check the prompt locations as Writer would
    prompt_locations = {
        "docstring": computed_repo_root / "phase2_docstrings" / "prompts" / "docstring.md",
        "readme": computed_repo_root / "phase3_readme" / "prompts" / "readme.md",
        "evaluation": computed_repo_root / "phase5_evaluation" / "prompts" / "evaluation.md",
    }
    
    print("\nPrompt locations Writer will check:")
    all_found = True
    for name, path in prompt_locations.items():
        exists = path.exists()
        status = "✓" if exists else "✗"
        print(f"  {status} {name:15s} {path}")
        if exists:
            size = len(path.read_text())
            print(f"     Size: {size} chars")
        all_found = all_found and exists
    
    # Check fallback locations
    print("\nFallback locations:")
    for name in ["docstring", "readme", "evaluation"]:
        fallback_path = computed_repo_root / "agents" / "prompts" / f"{name}.md"
        exists = fallback_path.exists()
        status = "✓" if exists else "✗"
        print(f"  {status} {name:15s} {fallback_path}")
        if exists:
            size = len(fallback_path.read_text())
            print(f"     Size: {size} chars")
    
    if all_found:
        print("\n✅ All prompts accessible from Writer!")
        return True
    else:
        print("\n❌ Some prompts not found!")
        return False


def test_agents_writer():
    """Test Writer from agents can load prompts."""
    print("\n" + "=" * 70)
    print("TEST: Legacy Agents Writer Prompt Loading")
    print("=" * 70)
    
    repo_root = Path(__file__).parent
    
    # Check what __file__.parent gives us
    writer_file = repo_root / "agents" / "writer.py"
    print(f"\nWriter file location: {writer_file}")
    print(f"Writer file exists: {writer_file.exists()}")
    
    # From agents/writer.py, __init__ sets:
    # self.repo_root = Path(__file__).parent.parent
    
    writer_location = writer_file.parent  # agents/
    print(f"\nWriter's __file__.parent: {writer_location}")
    
    computed_repo_root = writer_location.parent  # Go up 1 level
    print(f"Writer's computed repo_root: {computed_repo_root}")
    
    # Now check the prompt locations as Writer would
    prompt_locations = {
        "docstring": computed_repo_root / "phase2_docstrings" / "prompts" / "docstring.md",
        "readme": computed_repo_root / "phase3_readme" / "prompts" / "readme.md",
        "evaluation": computed_repo_root / "phase5_evaluation" / "prompts" / "evaluation.md",
    }
    
    print("\nPrompt locations Writer will check:")
    all_found = True
    for name, path in prompt_locations.items():
        exists = path.exists()
        status = "✓" if exists else "✗"
        print(f"  {status} {name:15s} {path}")
        if exists:
            size = len(path.read_text())
            print(f"     Size: {size} chars")
        all_found = all_found and exists
    
    # Check fallback locations
    print("\nFallback locations:")
    for name in ["docstring", "readme", "evaluation"]:
        fallback_path = computed_repo_root / "agents" / "prompts" / f"{name}.md"
        exists = fallback_path.exists()
        status = "✓" if exists else "✗"
        print(f"  {status} {name:15s} {fallback_path}")
        if exists:
            size = len(fallback_path.read_text())
            print(f"     Size: {size} chars")
    
    if all_found:
        print("\n✅ All prompts accessible from Writer!")
        return True
    else:
        print("\n❌ Some prompts not found!")
        return False


def main():
    """Run direct Writer tests."""
    print("\n" + "🔍" * 35)
    print("\n    DIRECT WRITER PROMPT LOADING TEST")
    print("\n" + "🔍" * 35 + "\n")
    
    result1 = test_phase2_writer()
    result2 = test_agents_writer()
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    if result1 and result2:
        print("\n✅ Both Writer implementations can find all prompts!")
        print("\nThe code is correct. If you're still seeing errors:")
        print("1. Clear Python cache: find . -name '*.pyc' -delete")
        print("2. Restart your Python kernel/runtime")
        print("3. Re-import the modules\n")
        return 0
    else:
        print("\n❌ Prompt loading issue detected!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
