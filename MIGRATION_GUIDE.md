# Migration Guide: Documentation Pipeline v2.0

This guide helps you migrate from the old pipeline API to the new refactored version with GPU optimization and router support.

## What Changed

### Major Improvements

1. **Memory Optimization for GPU**
   - 4-bit quantization support (reduces memory by ~75%)
   - Prompt truncation to avoid OOM
   - Smart device management
   - CUDA memory fragmentation reduction

2. **Flexible Model Loading**
   - SessionRouter for shared or per-agent models
   - Router reuse across multiple projects
   - Lazy loading and eviction strategies
   - No duplicate model loads

3. **Artifact-First Approach**
   - Three docstring modes: `none`, `modules_only`, `symbols_and_modules`
   - Skip LLM entirely for fastest processing
   - Generate only what you need

4. **Per-Role LLM Parameters**
   - Different generation params for each agent role
   - Backward-compatible with single `llm_params`

5. **Clean README Generation**
   - New curated README builder
   - Artifact-driven structure
   - Optional LLM for overview sections
   - Replaces MkDocs site generation

## API Changes

### Old API (v1.0)

```python
from main import run_pipeline

result = run_pipeline(
    repo_root="/content/Demo",
    artifacts_dir="/content/Artifacts",
    model_id="Qwen/Qwen2.5-Coder-3B-Instruct",
    llm_params={"temperature": 0.2, "max_new_tokens": 220},
    build_html=False,
    cleanup_cache=True,
    debug=True,
)
```

### New API (v2.0)

```python
from main import run_pipeline

result = run_pipeline(
    repo_root="/content/Demo",
    artifacts_dir="/content/Artifacts",
    model_id="Qwen/Qwen2.5-Coder-3B-Instruct",
    
    # NEW: Memory optimization (recommended for T4)
    quantize=True,              # 4-bit quantization
    max_input_tokens=2048,      # Truncate long prompts
    
    # NEW: Control LLM usage
    docstring_mode="modules_only",  # or "none", "symbols_and_modules"
    
    # NEW: Generate README instead of HTML site
    generate_readme=True,
    readme_use_llm=False,
    
    # Backward compatible
    llm_params={"temperature": 0.2, "max_new_tokens": 220},
    cleanup_cache=True,
    debug=True,
)
```

## Migration Scenarios

### Scenario 1: Basic Migration (Minimal Changes)

**Before:**
```python
run_pipeline(
    repo_root="/content/MyProject",
    artifacts_dir="/content/Artifacts",
    model_id="Qwen/Qwen2.5-Coder-3B-Instruct",
    llm_params={"temperature": 0.2},
    build_html=False,
)
```

**After (recommended):**
```python
run_pipeline(
    repo_root="/content/MyProject",
    artifacts_dir="/content/Artifacts",
    model_id="Qwen/Qwen2.5-Coder-3B-Instruct",
    quantize=True,              # Add for T4 compatibility
    docstring_mode="modules_only",  # Add to control LLM usage
    generate_readme=True,       # Add for README generation
    llm_params={"temperature": 0.2},
)
```

### Scenario 2: Advanced - Per-Role Parameters

**Before:**
```python
# All agents used same parameters
run_pipeline(
    repo_root="/content/MyProject",
    artifacts_dir="/content/Artifacts",
    model_id="Qwen/Qwen2.5-Coder-3B-Instruct",
    llm_params={"temperature": 0.2, "max_new_tokens": 220},
)
```

**After:**
```python
# Different parameters per role
run_pipeline(
    repo_root="/content/MyProject",
    artifacts_dir="/content/Artifacts",
    model_id="Qwen/Qwen2.5-Coder-3B-Instruct",
    quantize=True,
    llm_params_by_role={
        "writer": {"temperature": 0.2, "max_new_tokens": 220},
        "critic": {"temperature": 0.1, "max_new_tokens": 150},
        "readme": {"temperature": 0.3, "max_new_tokens": 300},
    },
    generate_readme=True,
    readme_use_llm=True,
)
```

### Scenario 3: Multiple Projects with Shared Model

**Before:**
```python
# Model loaded twice = OOM risk
for project in projects:
    run_pipeline(
        repo_root=project,
        artifacts_dir="/content/Artifacts",
        model_id="Qwen/Qwen2.5-Coder-3B-Instruct",
    )
```

**After:**
```python
from Utils.ToolBox.llm_clients.session_router import SessionRouter

# Load model once, reuse for all projects
router = SessionRouter(
    run_mode="shared",
    shared_model_id="Qwen/Qwen2.5-Coder-3B-Instruct",
    quantize=True,
    max_input_tokens=2048,
)

for project in projects:
    run_pipeline(
        repo_root=project,
        artifacts_dir="/content/Artifacts",
        router=router,  # Reuse loaded model
        docstring_mode="modules_only",
        generate_readme=True,
    )

router.cleanup()
```

### Scenario 4: Different Models per Agent

**New capability:**
```python
run_pipeline(
    repo_root="/content/MyProject",
    artifacts_dir="/content/Artifacts",
    run_mode="per_agent",
    agent_models={
        "writer": "Qwen/Qwen2.5-Coder-3B-Instruct",
        "critic": "Qwen/Qwen2.5-Coder-1.5B-Instruct",  # Lighter
        "readme": "Qwen/Qwen2.5-Coder-3B-Instruct",
    },
    keep_loaded=False,  # Unload after each agent
    quantize=True,
)
```

### Scenario 5: Fastest Mode (No LLM)

**New capability:**
```python
# Skip all LLM calls, just organize artifacts
run_pipeline(
    repo_root="/content/MyProject",
    artifacts_dir="/content/Artifacts",
    docstring_mode="none",  # No docstring generation
    generate_readme=True,    # But still create README
    readme_use_llm=False,    # Without LLM
)
```

## Deprecated Features

### MkDocs Site Generation

**Deprecated:**
```python
run_pipeline(
    build_html=True,  # DEPRECATED
)
```

**Use instead:**
```python
run_pipeline(
    generate_readme=True,  # Generates clean README
)
```

The MkDocs site generation (`build_docs_site.py`, `mkdocs_builder.py`) is deprecated but still available for backward compatibility. It will be removed in a future version.

## Configuration Reference

### PipelineConfig Changes

**Old attributes:**
- `llm_params` - Single dict for all agents

**New attributes:**
- `llm_params_by_role` - Per-role parameters (recommended)
- `llm_params` - Backward-compatible alias (maps to `llm_params_by_role["default"]`)
- `docstring_mode` - Control LLM usage: `"none"`, `"modules_only"`, `"symbols_and_modules"`

### SessionRouter

New class for managing LLM clients:

```python
SessionRouter(
    run_mode="shared",              # or "per_agent"
    shared_model_id="model-name",   # for "shared" mode
    agent_models={...},             # for "per_agent" mode
    device="auto",                  # "auto", "cpu", "cuda", "mps"
    dtype="auto",                   # "auto", "float16", "bfloat16", "float32"
    quantize=True,                  # 4-bit quantization
    max_input_tokens=2048,          # Truncate long inputs
    keep_loaded=True,               # Cache models vs evict
)
```

### HFClient

New parameters:
- `quantize: bool = False` - Enable 4-bit quantization
- `max_input_tokens: Optional[int] = None` - Truncate prompts

Environment variables automatically set:
- `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` - Reduce fragmentation

## Installation

### GPU Environment (Colab T4)

```bash
# Core dependencies
pip install transformers>=4.45.0 accelerate>=0.33.0 torch pydantic networkx

# Recommended: 4-bit quantization
pip install bitsandbytes>=0.41.0
```

### CPU-Only Environment

```bash
# Skip bitsandbytes (GPU-only)
pip install transformers>=4.45.0 accelerate>=0.33.0 torch pydantic networkx
```

## Troubleshooting

### OOM on T4

**Problem:** Out of memory even with 3B model

**Solution:**
```python
run_pipeline(
    quantize=True,              # Must be True
    max_input_tokens=1024,      # Reduce from default 2048
    docstring_mode="modules_only",  # Not "symbols_and_modules"
    keep_loaded=False,          # If using per_agent mode
)
```

### Import Errors

**Problem:** `AttributeError: 'PipelineConfig' object has no attribute 'llm_params'`

**Solution:** Update to latest version. The backward-compatible property was added in v2.0.

### Model Loading Twice

**Problem:** Model loads twice, causing OOM

**Solution:** Use `router` parameter to reuse loaded models:
```python
router = SessionRouter(run_mode="shared", shared_model_id="...", quantize=True)
run_pipeline(router=router, ...)
```

## Support

For issues or questions:
1. Check `examples.py` for comprehensive usage examples
2. Run `verify_refactor.py` to check your installation
3. Run `test_mock.py` to verify API compatibility

## Version History

- **v2.0** - Major refactor with GPU optimization, router support, and artifact-first approach
- **v1.0** - Initial POC with MkDocs site generation
