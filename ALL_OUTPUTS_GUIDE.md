# Complete Guide: Where Each Phase Saves Its Outputs

This guide shows exactly where each phase of the documentation pipeline saves its outputs.

## Quick Reference Table

| Phase | Output Type | Default Location | Configurable? |
|-------|------------|------------------|---------------|
| **Phase 1** | AST data | `./artifacts/ast.json` | ✅ via `artifacts_dir` |
| **Phase 1** | Dependencies | `./artifacts/dependencies_normalized.json` | ✅ via `artifacts_dir` |
| **Phase 1** | Components | `./artifacts/components.json` | ✅ via `artifacts_dir` |
| **Phase 1** | Edge cases | `./artifacts/edge_cases.json` | ✅ via `artifacts_dir` |
| **Phase 2** | Docstrings | `./artifacts/doc_artifacts.json` | ✅ via `artifacts_dir` |
| **Phase 2** | Cache | `./artifacts/cache/` | ✅ via `artifacts_dir` |
| **Phase 3** | README | `<repo_path>/README.md` | ❌ Fixed location |
| **Phase 4** | Validation | In-memory only | N/A |
| **Phase 5** | Evaluation | `./artifacts/evaluation_report.json` | ✅ via `artifacts_dir` |

---

## Detailed Output Information

### Phase 1: Static Code Analysis

**Purpose:** Extract code structure, dependencies, and components.

**Output Files:**

1. **`ast.json`**
   - **Location:** `<artifacts_dir>/ast.json`
   - **Contains:** Abstract syntax tree data for all source files
   - **Structure:**
     ```json
     {
       "module_path.py": {
         "file": "path/to/file.py",
         "language": "python",
         "imports": [...],
         "functions": [...],
         "classes": [...]
       }
     }
     ```
   - **Size:** Varies (typically 100KB - 10MB depending on repo size)

2. **`dependencies_normalized.json`**
   - **Location:** `<artifacts_dir>/dependencies_normalized.json`
   - **Contains:** Dependency graph with internal/external dependencies
   - **Structure:**
     ```json
     {
       "internal_dependencies": {
         "file1.py": ["file2.py", "file3.py"]
       },
       "external_dependencies": {
         "file1.py": ["numpy", "pandas"]
       },
       "raw_graph": {
         "nodes": [...],
         "edges": [...]
       }
     }
     ```

3. **`components.json`**
   - **Location:** `<artifacts_dir>/components.json`
   - **Contains:** Component clusters (groups of related files)
   - **Structure:**
     ```json
     {
       "components": [
         {
           "id": "component_0",
           "files": ["utils/helpers.py", "utils/validators.py"],
           "type": "utility"
         }
       ]
     }
     ```

4. **`edge_cases.json`** (Optional)
   - **Location:** `<artifacts_dir>/edge_cases.json`
   - **Contains:** Edge case analysis (circular imports, monolithic files, etc.)
   - **Enabled when:** `enable_edge_case_detection=True` in StructuralAgent
   - **Structure:**
     ```json
     {
       "circular_imports": [...],
       "monolithic_files": [...],
       "generated_code": [...]
     }
     ```

**How to Access:**
```python
phase1_results = orch.run_phase1()

# Output paths are in the results
ast_path = phase1_results.get("artifacts", {}).get("ast_path")
deps_path = phase1_results.get("artifacts", {}).get("deps_path")
components_path = phase1_results.get("artifacts", {}).get("components_path")

print(f"AST saved to: {ast_path}")
print(f"Dependencies saved to: {deps_path}")
print(f"Components saved to: {components_path}")
```

---

### Phase 2: Docstring Generation

**Purpose:** Generate Google-style docstrings for all modules, functions, and classes.

**Output Files:**

1. **`doc_artifacts.json`**
   - **Location:** `<artifacts_dir>/doc_artifacts.json`
   - **Contains:** Generated docstrings with metadata
   - **Structure:**
     ```json
     {
       "module_path.py": {
         "module_docstring": {
           "content": "Module description...",
           "cached": false
         },
         "functions": [
           {
             "name": "function_name",
             "docstring": "Function description...",
             "cached": false
           }
         ],
         "classes": [
           {
             "name": "ClassName",
             "docstring": "Class description...",
             "methods": [...]
           }
         ]
       }
     }
     ```
   - **Size:** Varies (typically 500KB - 50MB depending on codebase)

2. **`cache/`** (Directory)
   - **Location:** `<artifacts_dir>/cache/`
   - **Contains:** Cached LLM responses to avoid regeneration
   - **Structure:** Multiple subdirectories by cache category
   - **Benefits:** Speeds up subsequent runs, saves LLM costs

**How to Access:**
```python
phase2_results = orch.run_phase2()

# Output path is in the results
output_path = phase2_results["output_path"]
print(f"Docstrings saved to: {output_path}")

# Access the generated docstrings
docstrings = phase2_results["docstrings"]
print(f"Generated {phase2_results['stats']['total_generated']} docstrings")
```

**Console Output Example:**
```
━━━ PHASE 2: Docstrings ━━━
Processing 87 modules...
✅ 241 docstrings generated (20 cached, 221 new)
📄 Output saved to: /path/to/artifacts/doc_artifacts.json
```

---

### Phase 3: README Generation

**Purpose:** Generate a comprehensive README.md with 6 required sections.

**Output Files:**

1. **`README.md`**
   - **Location:** `<repo_path>/README.md` (in the root of your repository)
   - **Contains:** Complete README with:
     - Title
     - Overview
     - Features
     - Architecture
     - Installation
     - Usage
   - **Format:** Markdown
   - **Size:** Typically 5-20 KB

**How to Access:**
```python
phase3_results = orch.run_phase3()

# Output path is in the results
readme_path = phase3_results["readme_path"]
print(f"README saved to: {readme_path}")

# Access the content
readme_content = phase3_results["content"]
print(f"README has {len(readme_content)} characters")
```

**Console Output Example:**
```
━━━ PHASE 3: README ━━━
Generating README (6 sections)...
✅ README generated: /path/to/your/repo/README.md
```

**Note:** The README is saved directly to your repository root, NOT in the artifacts directory. This is intentional so it's immediately visible when browsing the repository.

---

### Phase 4: Validation

**Purpose:** Validate README sections and regenerate if needed.

**Output Files:**

⚠️ **No file output** - Validation results are returned in memory only.

**What You Get:**
```python
phase4_results = orch.run_phase4()

# Validation results structure
{
  "validation_results": {
    "title": {"valid": True, "issues": []},
    "overview": {"valid": True, "issues": []},
    "features": {"valid": False, "issues": ["Too short"]},
    ...
  },
  "all_valid": False,
  "updated_content": "..." # Only if regeneration occurred
}
```

**Console Output Example:**
```
━━━ PHASE 4: Validation ━━━
Validating 6 sections...
✅ title: Valid
✅ overview: Valid
⚠️ features: Too short
✅ architecture: Valid
✅ installation: Valid
✅ usage: Valid
```

**Note:** If validation finds issues and regenerates sections, the updated content is available in `phase4_results["updated_content"]`, but it's NOT automatically saved to disk. You need to manually save it if you want to keep the changes.

---

### Phase 5: Evaluation

**Purpose:** Evaluate documentation quality on 4 metrics.

**Output Files:**

1. **`evaluation_report.json`**
   - **Location:** `<artifacts_dir>/evaluation_report.json`
   - **Contains:** Quality scores and improvement suggestions
   - **Structure:**
     ```json
     {
       "clarity": 8,
       "completeness": 7,
       "consistency": 9,
       "usability": 8,
       "overall": 8.0,
       "strengths": [
         "Clear organization",
         "Good examples"
       ],
       "suggestions": [
         "Add more API documentation",
         "Include troubleshooting section"
       ]
     }
     ```
   - **Size:** Typically 1-5 KB

**How to Access:**
```python
phase5_results = orch.run_phase5()

# Output path is in the results
report_path = phase5_results["report_path"]
print(f"Evaluation saved to: {report_path}")

# Access the scores
evaluation = phase5_results["evaluation"]
print(f"Overall score: {evaluation['overall']}/10")
print(f"Clarity: {evaluation['clarity']}/10")
print(f"Completeness: {evaluation['completeness']}/10")
```

**Console Output Example:**
```
━━━ PHASE 5: Evaluation ━━━
Evaluating documentation...

📊 Score: 8.0/10
   Clarity: 8
   Completeness: 7
   Consistency: 9
   Usability: 8
   
📄 Report saved to: /path/to/artifacts/evaluation_report.json
```

---

## Customizing Output Locations

### Change Artifacts Directory

**Default:** `./artifacts`

**Customize:**
```python
from orchestrator import Orchestrator

orch = Orchestrator(
    repo_path="/path/to/repo",
    artifacts_dir="/custom/output/directory",  # Change this
    use_structural_agent=True
)

orch.run_all()
```

**Result:**
- Phase 1 outputs: `/custom/output/directory/ast.json`, etc.
- Phase 2 outputs: `/custom/output/directory/doc_artifacts.json`
- Phase 5 outputs: `/custom/output/directory/evaluation_report.json`
- Phase 3 README: Still saved to `<repo_path>/README.md` (cannot be changed)

### Access All Output Paths

```python
from orchestrator import Orchestrator

orch = Orchestrator(repo_path="./", artifacts_dir="./my_outputs")

# Run all phases
results = orch.run_all()

# Print all output locations
print("=" * 60)
print("OUTPUT LOCATIONS")
print("=" * 60)

# Phase 1
if "phase1" in results and "artifacts" in results["phase1"]:
    print("\nPhase 1 (Analysis):")
    for key, path in results["phase1"]["artifacts"].items():
        print(f"  {key}: {path}")

# Phase 2
if "phase2" in results:
    print("\nPhase 2 (Docstrings):")
    print(f"  output_path: {results['phase2']['output_path']}")

# Phase 3
if "phase3" in results:
    print("\nPhase 3 (README):")
    print(f"  readme_path: {results['phase3']['readme_path']}")

# Phase 4
print("\nPhase 4 (Validation):")
print("  (in-memory only, no file output)")

# Phase 5
if "phase5" in results:
    print("\nPhase 5 (Evaluation):")
    print(f"  report_path: {results['phase5']['report_path']}")

print("=" * 60)
```

---

## Complete Example

```python
from orchestrator import Orchestrator
from pathlib import Path
import json

# Initialize orchestrator
orch = Orchestrator(
    repo_path="/path/to/your/repo",
    artifacts_dir="./documentation_artifacts",
    model_id="Qwen/Qwen2.5-Coder-1.5B-Instruct",
    device="auto",
    quantize=True,
    use_structural_agent=True
)

# Run all phases
print("Running complete documentation pipeline...")
results = orch.run_all()

# Access all outputs
print("\n" + "=" * 60)
print("DOCUMENTATION PIPELINE COMPLETE!")
print("=" * 60)

# Phase 1 Outputs
print("\n📊 Phase 1: Static Analysis")
ast_path = Path(results["phase1"]["artifacts"]["ast_path"])
deps_path = Path(results["phase1"]["artifacts"]["deps_path"])
components_path = Path(results["phase1"]["artifacts"]["components_path"])
print(f"  AST data: {ast_path} ({ast_path.stat().st_size / 1024:.1f} KB)")
print(f"  Dependencies: {deps_path} ({deps_path.stat().st_size / 1024:.1f} KB)")
print(f"  Components: {components_path} ({components_path.stat().st_size / 1024:.1f} KB)")

# Phase 2 Outputs
print("\n📝 Phase 2: Docstrings")
doc_path = Path(results["phase2"]["output_path"])
print(f"  Docstrings: {doc_path} ({doc_path.stat().st_size / 1024:.1f} KB)")
print(f"  Generated: {results['phase2']['stats']['total_generated']} docstrings")
print(f"  Cached: {results['phase2']['stats']['cached']}")

# Phase 3 Outputs
print("\n📄 Phase 3: README")
readme_path = Path(results["phase3"]["readme_path"])
print(f"  README: {readme_path} ({readme_path.stat().st_size / 1024:.1f} KB)")

# Phase 4 Results (no file output)
print("\n✅ Phase 4: Validation")
print(f"  All sections valid: {results['phase4']['all_valid']}")

# Phase 5 Outputs
print("\n📊 Phase 5: Evaluation")
eval_path = Path(results["phase5"]["report_path"])
print(f"  Report: {eval_path} ({eval_path.stat().st_size / 1024:.1f} KB)")
print(f"  Overall score: {results['phase5']['evaluation']['overall']}/10")

print("\n" + "=" * 60)
print("All outputs saved successfully!")
print("=" * 60)

# Load and use the outputs
print("\n💡 Loading generated docstrings...")
with open(doc_path) as f:
    docstrings = json.load(f)
    print(f"  Found docstrings for {len(docstrings)} modules")

print("\n💡 Loading evaluation...")
with open(eval_path) as f:
    evaluation = json.load(f)
    print(f"  Strengths: {', '.join(evaluation.get('strengths', []))}")
```

---

## Summary

### Where Are My Files?

**If you used default settings:**
- Analysis data: `./artifacts/ast.json`, `dependencies_normalized.json`, `components.json`
- Docstrings: `./artifacts/doc_artifacts.json`
- README: `./README.md` (in your repo root)
- Evaluation: `./artifacts/evaluation_report.json`

**If you customized `artifacts_dir="/my/path"`:**
- Analysis data: `/my/path/ast.json`, `dependencies_normalized.json`, `components.json`
- Docstrings: `/my/path/doc_artifacts.json`
- README: `<repo_path>/README.md` (still in repo root)
- Evaluation: `/my/path/evaluation_report.json`

### Quick Check

```bash
# List all output files (assuming default artifacts_dir)
ls -lh ./artifacts/
# Should show:
# - ast.json
# - dependencies_normalized.json
# - components.json
# - doc_artifacts.json
# - evaluation_report.json
# - cache/ (directory)

# Check README
ls -lh ./README.md
```

---

## Need Help?

- **Can't find outputs?** Check the return value from each phase - it includes the output paths
- **Wrong location?** Verify your `artifacts_dir` parameter in Orchestrator
- **Missing files?** Make sure the phase completed successfully (check for errors)
- **Cache taking space?** The cache directory helps speed up subsequent runs but can be deleted safely

For more details on specific phases:
- Phase 1: See `phase1_analysis/README.md`
- Phase 2: See `PHASE2_OUTPUT_GUIDE.md`
- Phase 3: See `phase3_readme/README.md`
