# Phase 3 FileNotFoundError Fix

## Problem

Phase 3 (README generation) was failing with a FileNotFoundError:

```
━━━ PHASE 3: README ━━━
Generating README (6 sections)...
---------------------------------------------------------------------------
FileNotFoundError                         Traceback (most recent call last)
```

## Root Cause

After the project reorganization into phase-specific directories, the Writer class was looking for prompt files in the wrong location:

**What was happening:**
```python
# In phase2_docstrings/agents/writer.py
class Writer:
    def __init__(self, llm_client: LLMClient):
        self.prompts_dir = Path(__file__).parent / "prompts"  # ❌ Wrong!
        # This resolved to: phase2_docstrings/agents/prompts/ (doesn't exist)
```

**Where prompts actually are:**
- `phase2_docstrings/prompts/docstring.md` ✅
- `phase3_readme/prompts/readme.md` ✅
- `phase5_evaluation/prompts/evaluation.md` ✅

## Solution

Updated the `Writer` class in both locations to use phase-aware prompt loading:

### Changes Made

**1. phase2_docstrings/agents/writer.py**
**2. agents/writer.py** (legacy location)

```python
class Writer:
    def __init__(self, llm_client: LLMClient):
        # Store repository root instead of prompts_dir
        self.repo_root = Path(__file__).parent.parent  # or .parent.parent.parent
    
    def _load_prompt(self, name: str) -> str:
        """
        Load prompt template from phase-specific directories.
        """
        # Map prompt names to their phase locations
        prompt_locations = {
            "docstring": self.repo_root / "phase2_docstrings" / "prompts" / "docstring.md",
            "readme": self.repo_root / "phase3_readme" / "prompts" / "readme.md",
            "evaluation": self.repo_root / "phase5_evaluation" / "prompts" / "evaluation.md",
        }
        
        # Try phase-specific location first
        prompt_path = prompt_locations.get(name)
        if prompt_path and prompt_path.exists():
            return prompt_path.read_text()
        
        # Fallback to agents/prompts/ for backward compatibility
        fallback_path = self.repo_root / "agents" / "prompts" / f"{name}.md"
        if fallback_path.exists():
            return fallback_path.read_text()
        
        raise FileNotFoundError(f"Prompt '{name}' not found")
```

## Verification

✅ **All prompts are now accessible:**
```
✓ docstring: phase2_docstrings/prompts/docstring.md (690 chars)
✓ readme: phase3_readme/prompts/readme.md (1057 chars)
✓ evaluation: phase5_evaluation/prompts/evaluation.md (1134 chars)
```

✅ **Fallback locations available:**
```
✓ Fallback docstring: agents/prompts/docstring.md
✓ Fallback readme: agents/prompts/readme.md
✓ Fallback evaluation: agents/prompts/evaluation.md
```

## Impact

Phase 3 README generation will now work correctly. The fix:
- ✅ Finds prompts in phase-specific directories
- ✅ Falls back to legacy location for compatibility
- ✅ Provides clear error message if prompt not found
- ✅ Works with both new phase structure and old structure

## Testing

Run the orchestrator again:
```python
from orchestrator import Orchestrator

orch = Orchestrator(
    repo_path="./",
    artifacts_dir="./artifacts",
    use_structural_agent=True
)

# Phase 3 should now work
phase3_results = orch.run_phase3()
```

Expected output:
```
━━━ PHASE 3: README ━━━
Generating README (6 sections)...
✅ README generated: /path/to/repo/README.md
```

## Related Files

- `phase2_docstrings/agents/writer.py` - Updated Writer class
- `agents/writer.py` - Updated legacy Writer class
- `phase2_docstrings/prompts/docstring.md` - Docstring prompt
- `phase3_readme/prompts/readme.md` - README prompt
- `phase5_evaluation/prompts/evaluation.md` - Evaluation prompt
