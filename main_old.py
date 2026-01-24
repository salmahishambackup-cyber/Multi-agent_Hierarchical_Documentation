from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Literal, Optional

from Docsys.config import PipelineConfig, DocstringMode
from Docsys.generate_doc_artifacts import generate_doc_artifacts
from Docsys.build_readme import build_readme
from Utils.ToolBox.io_tools import project_key_from_repo_root, ensure_dir, rm_tree_safe
from Utils.ToolBox.llm_clients.session_router import SessionRouter


def run_pipeline(
    *,
    repo_root: str,
    artifacts_dir: str,
    model_id: Optional[str] = None,
    llm_params: Optional[Dict[str, Any]] = None,
    llm_params_by_role: Optional[Dict[str, Dict[str, Any]]] = None,
    device: str = "auto",
    dtype: str = "auto",
    docstring_mode: DocstringMode = "modules_only",
    insert_docstrings: bool = False,
    cleanup_cache: bool = True,
    debug: bool = True,
    # Router support
    router: Optional[SessionRouter] = None,
    run_mode: Literal["shared", "per_agent"] = "shared",
    agent_models: Optional[Dict[str, str]] = None,
    quantize: bool = True,
    max_input_tokens: Optional[int] = 2048,
    keep_loaded: bool = True,
    # README generation
    generate_readme: bool = True,
    readme_use_llm: bool = False,
) -> Dict[str, Any]:
    """
    Notebook-friendly pipeline entry point with GPU optimization for Colab T4.

    Args:
        repo_root: Path to target project containing source files referenced by ast.json.
        artifacts_dir: Root folder that contains per-project artifacts (Artifacts/<project_key>/...).
        model_id: Hugging Face model id (used if router not provided and run_mode="shared").
        llm_params: Dict of generation params (deprecated, use llm_params_by_role).
        llm_params_by_role: Dict mapping role -> generation params.
        device: auto|cpu|cuda|mps
        dtype: auto|float16|bfloat16|float32
        docstring_mode: "none"|"modules_only"|"symbols_and_modules" - controls LLM usage.
        insert_docstrings: If True, patches .py files in-place (LibCST).
        cleanup_cache: If True, removes Artifacts/cache/<project_key> after completion.
        debug: If True, writes intermediate artifacts and prints progress.
        
        # Router options (NEW):
        router: Optional pre-configured SessionRouter. If provided, ignores model_id/run_mode/agent_models.
        run_mode: "shared" (single model for all) or "per_agent" (lazy-load by role).
        agent_models: Dict mapping role -> model_id (for run_mode="per_agent").
        quantize: If True, use 4-bit quantization (default True for T4 compatibility).
        max_input_tokens: Max input tokens before truncation (default 2048).
        keep_loaded: If True, cache models; if False, evict after role usage.
        
        # README generation (NEW):
        generate_readme: If True, generate README.md in repo_root (default True).
        readme_use_llm: If True, use LLM for README overview section (default False).

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

    # Build llm_params_by_role
    params_by_role = llm_params_by_role or {}
    if llm_params and "default" not in params_by_role:
        params_by_role["default"] = llm_params
    if not params_by_role:
        params_by_role = {"default": {}}

    cfg = PipelineConfig(
        repo_root=repo_root_p,
        project_key=key,
        project_artifacts_dir=project_artifacts_dir,
        cache_dir=cache_dir,
        model_id=model_id or "",
        device=device,
        dtype=dtype,
        llm_params_by_role=params_by_role,
        docstring_mode=docstring_mode,
        insert_docstrings=insert_docstrings,
        debug=debug,
    )

    # Build or use provided router
    managed_router = False
    if router is None and docstring_mode != "none":
        if run_mode == "shared":
            if not model_id:
                raise ValueError("model_id required when run_mode='shared' and router not provided")
            router = SessionRouter(
                run_mode="shared",
                shared_model_id=model_id,
                device=device,
                dtype=dtype,
                quantize=quantize,
                max_input_tokens=max_input_tokens,
                keep_loaded=keep_loaded,
            )
        elif run_mode == "per_agent":
            if not agent_models:
                raise ValueError("agent_models required when run_mode='per_agent'")
            router = SessionRouter(
                run_mode="per_agent",
                agent_models=agent_models,
                device=device,
                dtype=dtype,
                quantize=quantize,
                max_input_tokens=max_input_tokens,
                keep_loaded=keep_loaded,
            )
        managed_router = True

    # Stage A: build doc_artifacts.json (artifact-first approach)
    stage_a = generate_doc_artifacts(cfg, router=router)

    # Stage B: generate README.md (optional)
    readme_path = None
    if generate_readme:
        readme_content = build_readme(
            cfg,
            stage_a["doc_artifacts"],
            router=router,
            use_llm=readme_use_llm,
        )
        readme_path = repo_root_p / "README.md"
        readme_path.write_text(readme_content, encoding="utf-8")
        if debug:
            print(f"[README] Generated: {readme_path}")

    # Cleanup
    if cleanup_cache:
        rm_tree_safe(cache_dir)
    
    if managed_router and router:
        router.cleanup()

    return {
        "project_key": key,
        "outputs": {
            "doc_plan": str(project_artifacts_dir / "doc_plan.json"),
            "doc_artifacts": str(project_artifacts_dir / "doc_artifacts.json"),
            "context_index": str(project_artifacts_dir / "context_index.json"),
            "quality_report": str(project_artifacts_dir / "quality_report.json"),
            "readme": str(readme_path) if readme_path else None,
            "cache_dir": str(cache_dir),
        },
    }