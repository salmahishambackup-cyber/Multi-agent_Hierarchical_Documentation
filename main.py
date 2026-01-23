from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from Docsys.config import PipelineConfig
from Docsys.generate_doc_artifacts import generate_doc_artifacts
from Docsys.build_docs_site import build_docs_site
from Docsys.mkdocs_builder import mkdocs_build_optional
from Utils.ToolBox.io_tools import project_key_from_repo_root, ensure_dir, rm_tree_safe


def run_pipeline(
    *,
    repo_root: str,
    artifacts_dir: str,
    model_id: str,
    llm_params: Optional[Dict[str, Any]] = None,
    device: str = "auto",
    dtype: str = "auto",
    insert_docstrings: bool = False,
    build_html: bool = False,
    cleanup_cache: bool = True,
    debug: bool = True,
) -> Dict[str, Any]:
    """
    Notebook-friendly pipeline entry point.

    Args:
        repo_root: Path to target project containing source files referenced by ast.json.
        artifacts_dir: Root folder that contains per-project artifacts (Artifacts/<project_key>/...).
        model_id: Hugging Face model id.
        llm_params: Dict of generation params: temperature, top_p, max_new_tokens, etc.
        device: auto|cpu|cuda|mps
        dtype: auto|float16|bfloat16|float32
        insert_docstrings: If True, patches .py files in-place (LibCST).
        build_html: If True, runs mkdocs build to produce static HTML site/.
        cleanup_cache: If True, removes Artifacts/cache/<project_key> after docs build.
        debug: If True, writes intermediate artifacts and prints progress.

    Returns:
        dict containing paths to generated artifacts and docs.
    """
    repo_root_p = Path(repo_root).resolve()
    artifacts_root = Path(artifacts_dir).resolve()
    key = project_key_from_repo_root(repo_root_p)

    project_artifacts_dir = artifacts_root / key
    cache_dir = artifacts_root / "cache" / key

    ensure_dir(project_artifacts_dir)
    ensure_dir(cache_dir)

    cfg = PipelineConfig(
        repo_root=repo_root_p,
        project_key=key,
        project_artifacts_dir=project_artifacts_dir,
        cache_dir=cache_dir,
        model_id=model_id,
        device=device,
        dtype=dtype,
        llm_params=llm_params or {},
        insert_docstrings=insert_docstrings,
        debug=debug,
    )

    # Stage A: build doc_artifacts.json (bridge contract)
    stage_a = generate_doc_artifacts(cfg)

    # Stage B: generate MkDocs Markdown site (no-import mode)
    stage_b = build_docs_site(cfg, stage_a)

    # Optional: build static HTML
    site_out = None
    if build_html:
        site_out = mkdocs_build_optional(cfg, stage_b["mkdocs_root"])

    # Optional: cleanup cache (keep generated docs/artifacts)
    if cleanup_cache:
        rm_tree_safe(cache_dir)

    return {
        "project_key": key,
        "outputs": {
            "doc_plan": str(project_artifacts_dir / "doc_plan.json"),
            "doc_artifacts": str(project_artifacts_dir / "doc_artifacts.json"),
            "context_index": str(project_artifacts_dir / "context_index.json"),
            "quality_report": str(project_artifacts_dir / "quality_report.json"),
            "mkdocs_root": str(stage_b["mkdocs_root"]),
            "mkdocs_yml": str(stage_b["mkdocs_yml"]),
            "site_html": site_out,
            "cache_dir": str(cache_dir),
        },
    }