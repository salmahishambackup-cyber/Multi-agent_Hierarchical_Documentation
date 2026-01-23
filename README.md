# Multi Agent Doc (POC)

This repository is a proof-of-concept for a **multi-agent, artifact-driven** system that:
1) Reads structural artifacts (`ast.json`, `dependencies_normalized.json`, `components.json`)
2) Slices code by byte offsets to generate **Google-style docstrings**
3) Produces a **no-import** documentation site (MkDocs-compatible Markdown + optional static HTML)

## Key features
- Dependency-aware traversal (topological order of modules)
- Incremental caching by code hash (dynamic-programming-like)
- Debuggable: saves `doc_plan.json`, `doc_artifacts.json`, `quality_report.json`
- Notebook-friendly: Python calls (no CLI required)
- Optional in-place docstring insertion (off by default)

## Quickstart (Notebook/Colab)
```python
from main import run_pipeline

result = run_pipeline(
    repo_root="/content/Demo",
    artifacts_dir="/content/Multi_Agent_Doc/Artifacts",
    model_id="Qwen/Qwen2.5-Coder-3B-Instruct",
    llm_params={"temperature": 0.2, "top_p": 0.95, "max_new_tokens": 220},
    build_html=False,              # set True if mkdocs-material is installed
    insert_docstrings=False,       # set True to patch .py files in-place (LibCST)
    cleanup_cache=True,            # remove cache after docs output
    debug=True,
)
print(result["outputs"])
```

## Where outputs go
Project key = folder name of `repo_root` (e.g., `/content/Demo` -> `Demo`).

Artifacts and outputs are written to:
- `Artifacts/<project_key>/doc_artifacts.json`
- `Artifacts/<project_key>/doc_plan.json`
- `Artifacts/<project_key>/quality_report.json`
- `Artifacts/<project_key>/docs/` (MkDocs Markdown site)

Cache (optional) is stored under:
- `Artifacts/cache/<project_key>/...`