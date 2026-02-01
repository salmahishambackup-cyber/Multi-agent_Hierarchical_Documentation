# Output Locations - Quick Reference Card

## Default Output Locations (with `artifacts_dir="./artifacts"`)

| Phase | What | Location | Format |
|-------|------|----------|--------|
| **1** | AST data | `./artifacts/ast.json` | JSON |
| **1** | Dependencies | `./artifacts/dependencies_normalized.json` | JSON |
| **1** | Components | `./artifacts/components.json` | JSON |
| **1** | Edge cases | `./artifacts/edge_cases.json` | JSON (optional) |
| **2** | Docstrings | `./artifacts/doc_artifacts.json` | JSON |
| **2** | Cache | `./artifacts/cache/` | Directory |
| **3** | README | `<repo_path>/README.md` | Markdown |
| **4** | Validation | (in-memory only) | N/A |
| **5** | Evaluation | `./artifacts/evaluation_report.json` | JSON |

## Quick Access Code

```python
from orchestrator import Orchestrator

# Run pipeline
orch = Orchestrator(repo_path="./", artifacts_dir="./artifacts")
results = orch.run_all()

# Access output paths
phase1_ast = results["phase1"]["artifacts"]["ast_path"]
phase1_deps = results["phase1"]["artifacts"]["deps_path"]
phase1_components = results["phase1"]["artifacts"]["components_path"]

phase2_docs = results["phase2"]["output_path"]

phase3_readme = results["phase3"]["readme_path"]

# Phase 4 has no file output

phase5_eval = results["phase5"]["report_path"]

# Print all locations
print(f"AST: {phase1_ast}")
print(f"Dependencies: {phase1_deps}")
print(f"Components: {phase1_components}")
print(f"Docstrings: {phase2_docs}")
print(f"README: {phase3_readme}")
print(f"Evaluation: {phase5_eval}")
```

## Custom Artifacts Directory

```python
# Use custom location
orch = Orchestrator(
    repo_path="/path/to/repo",
    artifacts_dir="/custom/output/dir"  # <-- Change this
)

# Outputs will be at:
# - /custom/output/dir/ast.json
# - /custom/output/dir/dependencies_normalized.json
# - /custom/output/dir/components.json
# - /custom/output/dir/doc_artifacts.json
# - /custom/output/dir/evaluation_report.json
# - /path/to/repo/README.md (README location never changes)
```

## Check If Files Exist

```bash
# Assuming default artifacts_dir="./artifacts"

# Phase 1 outputs
ls -lh ./artifacts/ast.json
ls -lh ./artifacts/dependencies_normalized.json
ls -lh ./artifacts/components.json
ls -lh ./artifacts/edge_cases.json  # May not exist if not enabled

# Phase 2 outputs
ls -lh ./artifacts/doc_artifacts.json
ls -lh ./artifacts/cache/

# Phase 3 output
ls -lh ./README.md

# Phase 5 output
ls -lh ./artifacts/evaluation_report.json
```

## Python Check

```python
from pathlib import Path

artifacts_dir = Path("./artifacts")

# Check which files exist
files_to_check = [
    ("Phase 1 AST", artifacts_dir / "ast.json"),
    ("Phase 1 Dependencies", artifacts_dir / "dependencies_normalized.json"),
    ("Phase 1 Components", artifacts_dir / "components.json"),
    ("Phase 2 Docstrings", artifacts_dir / "doc_artifacts.json"),
    ("Phase 3 README", Path("./README.md")),
    ("Phase 5 Evaluation", artifacts_dir / "evaluation_report.json"),
]

print("File Check:")
for name, path in files_to_check:
    status = "✅ Exists" if path.exists() else "❌ Missing"
    size = f"({path.stat().st_size / 1024:.1f} KB)" if path.exists() else ""
    print(f"  {name}: {status} {size}")
```

## File Sizes (Typical)

- **ast.json**: 100 KB - 10 MB (depends on repo size)
- **dependencies_normalized.json**: 10 KB - 5 MB
- **components.json**: 5 KB - 500 KB
- **doc_artifacts.json**: 100 KB - 50 MB (depends on codebase)
- **README.md**: 5 KB - 20 KB
- **evaluation_report.json**: 1 KB - 5 KB

## Troubleshooting

**"I can't find my outputs!"**

1. Check the return value from each phase - it includes the output path
2. Verify your `artifacts_dir` parameter
3. Look at the console output - paths are printed after each phase
4. Run the Python check code above

**"Files are in the wrong location!"**

- Make sure you're using the correct `artifacts_dir` parameter
- README is ALWAYS saved to `<repo_path>/README.md`, not artifacts directory
- Cache is ALWAYS at `<artifacts_dir>/cache/`

**"Phase 4 has no output file!"**

- This is correct! Phase 4 (validation) only returns results in memory
- If you need to save validation results, do it manually:
  ```python
  import json
  phase4_results = orch.run_phase4()
  with open("./artifacts/validation_results.json", "w") as f:
      json.dump(phase4_results, f, indent=2)
  ```

## See Also

- **ALL_OUTPUTS_GUIDE.md** - Comprehensive guide with examples and detailed information
- **PHASE2_OUTPUT_GUIDE.md** - Detailed Phase 2 docstring output information
- **orchestrator.py** - Each method has output locations in its docstring

---

**Quick Help:**

```python
# Show all outputs after running pipeline
from orchestrator import Orchestrator

orch = Orchestrator(repo_path="./")
orch.run_all()  # Will print summary of all locations at the end!
```
