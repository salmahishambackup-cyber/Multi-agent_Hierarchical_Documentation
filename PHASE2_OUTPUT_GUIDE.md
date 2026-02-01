# Phase 2 Output Guide

## Where is Phase 2 Output Saved?

### Default Location
Phase 2 (Docstring Generation) saves its output to:

```
<artifacts_dir>/doc_artifacts.json
```

**Default path:** `./artifacts/doc_artifacts.json`

### How to Find It

When you run the orchestrator:

```python
from orchestrator import Orchestrator

orch = Orchestrator(
    repo_path="/path/to/repo",
    artifacts_dir="./artifacts"  # Default location
)

phase2_results = orch.run_phase2()
print(phase2_results["output_path"])  # Prints the exact path
```

The output path is returned in the results:
```python
{
    "output_path": "/full/path/to/artifacts/doc_artifacts.json",
    "stats": {...},
    "docstrings": {...}
}
```

### Customizing the Output Location

You can change where Phase 2 saves its output by setting the `artifacts_dir` parameter:

```python
# Save to a custom directory
orch = Orchestrator(
    repo_path="/path/to/repo",
    artifacts_dir="/custom/output/directory"  # Custom location
)

# Output will be saved to: /custom/output/directory/doc_artifacts.json
```

## Output File Structure

The `doc_artifacts.json` file contains docstrings for all modules, functions, and classes:

```json
{
    "path/to/module.py": {
        "module_docstring": {
            "docstring": "Module description...",
            "cached": false,
            "generated_at": "2024-01-01T12:00:00"
        },
        "functions": [
            {
                "name": "function_name",
                "docstring": "Function description...",
                "cached": false,
                "generated_at": "2024-01-01T12:00:00"
            }
        ],
        "classes": [
            {
                "name": "ClassName",
                "docstring": "Class description...",
                "cached": false,
                "generated_at": "2024-01-01T12:00:00"
            }
        ]
    }
}
```

### Structure Details

**For each module:**
- `module_docstring`: Docstring for the module itself
- `functions`: Array of docstrings for all functions in the module
- `classes`: Array of docstrings for all classes in the module

**For each docstring:**
- `name`: Name of the function/class (not included for module)
- `docstring`: The generated Google-style docstring text
- `cached`: Whether this was retrieved from cache (true) or newly generated (false)
- `generated_at`: Timestamp when the docstring was generated

## Additional Output

### Cache Directory

Phase 2 also uses a cache directory to store LLM responses for faster re-runs:

```
<artifacts_dir>/cache/
```

**Default path:** `./artifacts/cache/`

This directory contains cached LLM responses keyed by:
- Module path
- Code content
- Context used for generation

The cache speeds up subsequent runs by avoiding redundant LLM calls for unchanged code.

## Finding Output After Running

### Method 1: Check Return Value

```python
phase2_results = orch.run_phase2()
output_path = phase2_results["output_path"]
print(f"Phase 2 output saved to: {output_path}")
```

### Method 2: Check Console Output

When Phase 2 completes, it prints:
```
Processing 87 modules...
✅ 241 docstrings generated (0 cached, 241 new)
```

The file is saved to `<artifacts_dir>/doc_artifacts.json`

### Method 3: Look for the File

```bash
# Default location
ls -lh ./artifacts/doc_artifacts.json

# Or search for it
find . -name "doc_artifacts.json"
```

## Output Statistics

The return value also includes statistics:

```python
{
    "output_path": "/path/to/artifacts/doc_artifacts.json",
    "stats": {
        "total": 241,      # Total docstrings generated
        "cached": 0,       # Number from cache
        "generated": 241   # Number newly generated
    },
    "docstrings": {...}  # Full docstring data
}
```

## Code Reference

The output path is defined in:
- **File:** `phase2_docstrings/docstring_generator.py`
- **Line:** 106
- **Code:**
  ```python
  output_path = self.artifacts_dir / "doc_artifacts.json"
  write_json(output_path, results)
  ```

## Example Usage

### Full Example

```python
from orchestrator import Orchestrator

# Create orchestrator with custom artifacts directory
orch = Orchestrator(
    repo_path="/path/to/my/repo",
    artifacts_dir="./my_docs_output",  # Custom output directory
    model_id="Qwen/Qwen2.5-Coder-1.5B-Instruct",
    use_structural_agent=True
)

# Run Phase 1 first (required)
phase1_results = orch.run_phase1()

# Run Phase 2
phase2_results = orch.run_phase2()

# Get the output path
output_path = phase2_results["output_path"]
print(f"✅ Docstrings saved to: {output_path}")
# Output: ✅ Docstrings saved to: /path/to/my_docs_output/doc_artifacts.json

# Get statistics
stats = phase2_results["stats"]
print(f"Generated {stats['total']} docstrings ({stats['cached']} from cache)")
```

### Reading the Output

```python
import json
from pathlib import Path

# Read the generated docstrings
output_path = Path("./artifacts/doc_artifacts.json")
with open(output_path) as f:
    docstrings = json.load(f)

# Access docstrings for a specific module
module_path = "path/to/module.py"
if module_path in docstrings:
    module_doc = docstrings[module_path]["module_docstring"]["docstring"]
    print(f"Module docstring:\n{module_doc}")
    
    # List all functions
    for func in docstrings[module_path]["functions"]:
        print(f"\nFunction {func['name']}:")
        print(func["docstring"])
```

## Summary

| Item | Default Location |
|------|------------------|
| **Main Output** | `./artifacts/doc_artifacts.json` |
| **Cache Directory** | `./artifacts/cache/` |
| **Customizable via** | `artifacts_dir` parameter in Orchestrator |
| **Format** | JSON |
| **Contains** | Module, function, and class docstrings |

To find your Phase 2 output:
1. Check the `artifacts_dir` you specified (default: `./artifacts`)
2. Look for `doc_artifacts.json` in that directory
3. Or check the `output_path` key in the Phase 2 results
