# Summary: Output Location Documentation

## What Was Added

This commit adds comprehensive documentation answering the question: **"Where is each phase's output saved?"**

## Documentation Files

### 1. OUTPUT_LOCATIONS_QUICK_REF.md ⚡
**Best for:** Quick lookups, copy-paste code

**Contains:**
- Quick reference table
- Simple code examples
- Bash commands to check files
- Troubleshooting tips
- 5-minute read

**Use when:** You just need to find a file quickly

### 2. ALL_OUTPUTS_GUIDE.md 📚
**Best for:** Understanding the system, detailed information

**Contains:**
- Comprehensive explanations
- File structure details
- Complete code examples
- Customization guide
- Typical file sizes
- 15-minute read

**Use when:** You want to understand the full picture

### 3. In-Code Documentation 💻
**Location:** `orchestrator.py`

**Contains:**
- Docstrings for each `run_phaseX()` method
- Print statements showing output paths
- Summary output at end of `run_all()`

**Use when:** You're coding and want inline reference

## Quick Answer

### Default Locations (with `artifacts_dir="./artifacts"`)

```
./artifacts/
├── ast.json                          # Phase 1
├── dependencies_normalized.json      # Phase 1
├── components.json                   # Phase 1
├── edge_cases.json                   # Phase 1 (optional)
├── doc_artifacts.json                # Phase 2
├── cache/                            # Phase 2
│   └── ... (cached LLM responses)
└── evaluation_report.json            # Phase 5

./README.md                           # Phase 3 (in repo root!)
```

### In Memory Only

- **Phase 4 (Validation):** No file output, results only in return value

## How to Access Outputs

### Method 1: Return Values (Programmatic)

```python
from orchestrator import Orchestrator

orch = Orchestrator(repo_path="./")
results = orch.run_all()

# Access paths from return values
ast_path = results["phase1"]["artifacts"]["ast_path"]
docs_path = results["phase2"]["output_path"]
readme_path = results["phase3"]["readme_path"]
eval_path = results["phase5"]["report_path"]
```

### Method 2: Console Output (Visual)

When you run `orch.run_all()`, you'll see:

```
🤖 Documentation Assistant
Project: MyProject
Path: /path/to/repo
Artifacts Directory: /path/to/artifacts

━━━ PHASE 1: Analysis ━━━
[...]
📁 Phase 1 outputs saved to:
   • ast_path: /path/to/artifacts/ast.json
   • deps_path: /path/to/artifacts/dependencies_normalized.json
   • components_path: /path/to/artifacts/components.json

━━━ PHASE 2: Docstrings ━━━
[...]
📁 Phase 2 output saved to: /path/to/artifacts/doc_artifacts.json

━━━ PHASE 3: README ━━━
[...]
✅ README generated: /path/to/repo/README.md

━━━ PHASE 4: Validation ━━━
[...]
📋 Phase 4 validation results (in-memory, no file saved)

━━━ PHASE 5: Evaluation ━━━
[...]
📁 Phase 5 output saved to: /path/to/artifacts/evaluation_report.json

======================================================================
🎉 DOCUMENTATION PIPELINE COMPLETE!
======================================================================

📂 All Output Locations:

  Phase 1 (Analysis):
    • ast_path: /path/to/artifacts/ast.json
    • deps_path: /path/to/artifacts/dependencies_normalized.json
    • components_path: /path/to/artifacts/components.json

  Phase 2 (Docstrings):
    • docstrings: /path/to/artifacts/doc_artifacts.json
    • cache: /path/to/artifacts/cache

  Phase 3 (README):
    • README: /path/to/repo/README.md

  Phase 4 (Validation):
    • (in-memory only, no file output)

  Phase 5 (Evaluation):
    • report: /path/to/artifacts/evaluation_report.json

======================================================================
💡 See ALL_OUTPUTS_GUIDE.md for detailed information about each output
======================================================================
```

### Method 3: File System (Manual)

```bash
# List all artifacts (default location)
ls -lh ./artifacts/

# Check specific files
ls -lh ./artifacts/ast.json
ls -lh ./artifacts/doc_artifacts.json
ls -lh ./README.md
ls -lh ./artifacts/evaluation_report.json
```

## Customization

To change the artifacts directory:

```python
orch = Orchestrator(
    repo_path="/path/to/repo",
    artifacts_dir="/custom/output/dir"  # Your custom path
)
```

All artifacts will be saved to `/custom/output/dir/` instead of `./artifacts/`.

**Note:** README is always saved to `<repo_path>/README.md` (cannot be changed)

## Which Documentation Should I Read?

| Your Need | Read This |
|-----------|-----------|
| "Where is file X?" | OUTPUT_LOCATIONS_QUICK_REF.md |
| "How do I access outputs in code?" | OUTPUT_LOCATIONS_QUICK_REF.md |
| "What's in each file?" | ALL_OUTPUTS_GUIDE.md |
| "How do I customize locations?" | ALL_OUTPUTS_GUIDE.md |
| "Can I change the README location?" | ALL_OUTPUTS_GUIDE.md (Answer: No) |
| "Where's the cache?" | OUTPUT_LOCATIONS_QUICK_REF.md |
| "Why doesn't Phase 4 save a file?" | ALL_OUTPUTS_GUIDE.md |
| "What are typical file sizes?" | OUTPUT_LOCATIONS_QUICK_REF.md |
| "Quick code example?" | OUTPUT_LOCATIONS_QUICK_REF.md |
| "Complete usage example?" | ALL_OUTPUTS_GUIDE.md |

## Key Takeaways

1. ✅ **Phase 1-2, 5:** Save to `artifacts_dir` (default: `./artifacts/`)
2. ✅ **Phase 3:** Saves to repo root (`<repo_path>/README.md`)
3. ✅ **Phase 4:** No file output (in-memory only)
4. ✅ **All paths** are available in the return value from each phase
5. ✅ **Console output** shows paths in real-time as phases complete
6. ✅ **Summary** is printed at end of `run_all()`

## Files Modified/Created

### New Files
- `ALL_OUTPUTS_GUIDE.md` - Comprehensive guide (13,848 chars)
- `OUTPUT_LOCATIONS_QUICK_REF.md` - Quick reference (4,830 chars)
- `OUTPUT_LOCATION_SUMMARY.md` - This file (summary)

### Modified Files
- `orchestrator.py` - Added output documentation and print statements

### Total Documentation
- ~20,000 characters of documentation
- Multiple formats for different use cases
- Code examples and troubleshooting

## Next Steps for Users

1. **Run the pipeline:**
   ```python
   from orchestrator import Orchestrator
   orch = Orchestrator(repo_path="./")
   orch.run_all()
   ```

2. **Check the summary** printed at the end - it shows all output locations

3. **If you need details** about a specific file:
   - Quick lookup: See `OUTPUT_LOCATIONS_QUICK_REF.md`
   - Detailed info: See `ALL_OUTPUTS_GUIDE.md`

4. **Access outputs programmatically:**
   ```python
   # The return value contains all paths
   results = orch.run_all()
   print(results["phase2"]["output_path"])  # Docstrings location
   ```

---

**Remember:** The orchestrator now prints output locations automatically, so you don't need to memorize anything - just run it and watch the console output! 🎉
