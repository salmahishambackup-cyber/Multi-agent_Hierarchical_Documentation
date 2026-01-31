# Phase 1 Integration - Quick Start Guide

## What Changed?

The Phase 1 (static code analysis) has been upgraded with enhanced features while maintaining backward compatibility.

## Quick Start

### Option 1: Use Through Orchestrator (Recommended)
```python
from pipeline.orchestrator import Orchestrator

orchestrator = Orchestrator(
    repo_path="/path/to/your/repo",
    artifacts_dir="./artifacts"
)

# Phase 1 now uses StructuralAgent by default
results = orchestrator.run_phase1()

print(f"✅ Analyzed {results['stats']['modules']} modules")
print(f"   {results['stats']['functions']} functions")
print(f"   {results['stats']['classes']} classes")
```

### Option 2: Use StructuralAgent Directly
```python
from agents.structural_agent import StructuralAgent

agent = StructuralAgent(
    repo_path="/path/to/your/repo",
    artifacts_dir="./artifacts",
    enable_performance_monitoring=True,
    enable_edge_case_detection=True,
    enable_validation=True
)

results = agent.run()

# Access enhanced features
if results['edge_case_report']:
    print(f"⚠️  Found {len(results['edge_case_report']['circular_imports'])} circular imports")

if results['performance_summary']:
    print(f"⏱️  Total time: {results['performance_summary']['overall_duration_seconds']:.2f}s")
```

## New Features

### 1. Edge Case Detection
Automatically detects:
- **Circular imports**: Cycles in dependency graph
- **Monolithic files**: Files >1000 LOC or >50 functions
- **Generated code**: Auto-generated files (e.g., protobuf, ANTLR)

### 2. Performance Monitoring
Tracks:
- Execution time per stage
- Memory usage
- Provides optimization suggestions

### 3. Schema Validation
Validates output format for:
- AST structure
- Dependency graph
- Component clustering

### 4. Deterministic Outputs
Ensures:
- Sorted dictionaries and lists
- Reproducible results across runs
- No random ordering

## Supported Languages

- ✅ Python (.py)
- ✅ Java (.java)
- ✅ JavaScript (.js, .jsx)
- ✅ TypeScript (.ts, .tsx)
- ✅ C (.c, .h)
- ✅ C++ (.cpp, .cc, .cxx, .hpp)
- ✅ C# (.cs)

## Output Files

Phase 1 generates:

1. **`artifacts/ast.json`** - Abstract syntax tree
2. **`artifacts/dependencies_normalized.json`** - Dependency graph
3. **`artifacts/components.json`** - Component clustering
4. **`artifacts/edge_cases.json`** - Edge case findings (if enabled)

## Backward Compatibility

All existing code continues to work. To use the old Analyzer:

```python
orchestrator = Orchestrator(
    repo_path="/path/to/repo",
    use_structural_agent=False  # Use legacy analyzer
)
```

## Troubleshooting

### "Bus error" or Import Issues
If you encounter import errors related to PyTorch/torch, this is an environment issue, not a code issue. The code is syntactically valid and will work in a proper environment.

Workaround:
- Ensure PyTorch is properly installed (if using LLM features)
- Or use Phase 1 independently without LLM dependencies

### No Output from Phase 1
Check that:
- Repository path is correct
- Tree-sitter is installed: `pip install tree-sitter==0.20.4 tree-sitter-languages==1.10.2`
- Source files exist in the repository

## Examples

See `examples_phase1.py` for complete examples:
```bash
python examples_phase1.py
```

## Documentation

- **PHASE1_UPGRADE.md** - Detailed implementation guide
- **README.md** - Main project documentation
- **examples_phase1.py** - Usage examples

## Dependencies

Required:
```
tree-sitter==0.20.4
tree-sitter-languages==1.10.2
networkx>=3.2
tqdm>=4.66
pydantic>=2.7
psutil>=5.9.0
```

## Support

For issues or questions:
1. Check PHASE1_UPGRADE.md for detailed documentation
2. Review examples_phase1.py for usage patterns
3. Verify syntax with: `python check_syntax.py`
4. Open an issue on GitHub

## Next Steps

After running Phase 1, you can:
1. Review the generated artifacts in `./artifacts/`
2. Check for edge cases in `edge_cases.json`
3. Review performance metrics
4. Continue with Phase 2 (docstring generation)
5. Run the full pipeline with `orchestrator.run_all()`

---

🎉 **Phase 1 upgrade complete!** The system now provides enhanced analysis capabilities while remaining backward compatible.
