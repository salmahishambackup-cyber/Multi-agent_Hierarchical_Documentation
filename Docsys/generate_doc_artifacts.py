from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from Agents.Core.planner_agent import PlannerAgent
from Agents.Core.extractor_agent import ExtractorAgent
from Agents.Core.context_agent import ContextAgent
from Agents.Core.writer_agent import WriterAgent
from Agents.Core.critic_agent import CriticAgent

from Docsys.schemas import DocArtifacts, ModuleDoc, SymbolDoc, QualityReport
from Utils.ToolBox.artifact_loader import load_project_artifacts
from Utils.ToolBox.io_tools import write_json, append_jsonl
from Utils.ToolBox.context_tools import one_line_summary
from Utils.ToolBox.llm_clients.session_router import SessionRouter
from Utils.ToolBox.hashing_tools import sha256_text

# Optional in-place insertion
from Utils.ToolBox.docstring_inserter import insert_docstrings_inplace_optional


def generate_doc_artifacts(cfg, router: Optional[SessionRouter] = None) -> Dict[str, Any]:
    """
    Stage A:
      Artifacts + repo code -> doc_artifacts.json, doc_plan.json, context_index.json, quality_report.json
      
    Args:
        cfg: PipelineConfig with docstring_mode, llm_params_by_role, etc.
        router: Optional SessionRouter to reuse existing models
    """
    # Load analyzer artifacts from Artifacts/<project_key>/
    artifacts = load_project_artifacts(cfg.project_artifacts_dir)
    ast_json = artifacts["ast"]
    deps_json = artifacts["deps"]
    components_json = artifacts["components"]

    planner = PlannerAgent()
    plan = planner.build_plan(project_key=cfg.project_key, ast_json=ast_json, deps_json=deps_json)
    write_json(cfg.project_artifacts_dir / "doc_plan.json", plan.model_dump())

    extractor = ExtractorAgent(repo_root=cfg.repo_root)
    context_agent = ContextAgent(max_context_chars=int(cfg.llm_params.get("max_context_chars", 7000)))

    # Decide if we need LLM at all
    needs_llm = cfg.docstring_mode != "none"
    writer = None
    critic = None
    
    if needs_llm:
        # Use router if provided, otherwise create local client
        if router:
            writer_client = router.get_client("writer")
            critic_client = router.get_client("critic")
        else:
            from Utils.ToolBox.llm_clients.hf_client import HFClient
            hf = HFClient(model_id=cfg.model_id, device=cfg.device, dtype=cfg.dtype)
            writer_client = hf
            critic_client = hf
        
        writer = WriterAgent(hf=writer_client, google_prompt_path=Path("Agents/Prompts/google_docstring.md"))
        critic = CriticAgent(hf=critic_client, critic_prompt_path=Path("Agents/Prompts/critic_rules.md"))

    # caches (DP-style)
    symbol_cache_path = cfg.cache_dir / "symbol_cache.jsonl"
    module_cache_path = cfg.cache_dir / "module_cache.jsonl"

    dependency_summary_cache: Dict[str, str] = {}

    ast_entries = {e["file"]: e for e in ast_json["data"]}
    modules_out = []
    quality_issues = []

    if cfg.debug:
        print(f"[Stage A] Project: {cfg.project_key}")
        print(f"[Stage A] Modules planned: {len(plan.module_order)} | Tasks: {len(plan.tasks)}")

    for module_path in plan.module_order:
        entry = ast_entries.get(module_path)
        if not entry:
            continue

        # Build module-level context
        comp_hint = context_agent.component_hint(module_path, components_json)
        role_hint = context_agent.module_role_hint(module_path)
        context_lines = context_agent.build_context_lines(
            module_path=module_path,
            component_hint=comp_hint,
            role_hint=role_hint,
            dependency_summary_cache=dependency_summary_cache,
        )

        module_stub = extractor.module_stub(entry)
        module_hash = sha256_text(module_stub)

        if cfg.debug:
            print("\n" + "=" * 80)
            print(f"MODULE: {module_path}")
            print("=" * 80)

        # Generate module docstring if needed
        module_doc = ""
        if cfg.docstring_mode in ("modules_only", "symbols_and_modules") and writer:
            module_prompt = writer.build_prompt(
                kind="module",
                module_path=module_path,
                symbol=f"module:{module_path}",
                code_slice=module_stub,
                context_lines=context_lines,
            )
            writer_params = cfg.llm_params_by_role.get("writer", cfg.llm_params)
            module_doc = writer.generate_docstring(prompt=module_prompt, llm_params=writer_params)

            # cache module summary for downstream context
            dependency_summary_cache[f"module:{module_path}"] = one_line_summary(module_doc)

            append_jsonl(module_cache_path, {"module_path": module_path, "code_hash": module_hash, "docstring": module_doc})

        symbols_out = []

        # Generate symbol docs only if symbols_and_modules mode
        if cfg.docstring_mode == "symbols_and_modules" and writer and critic:
            # functions
            for fn in entry.get("functions", []):
                sym = _gen_symbol(cfg, extractor, writer, critic, module_path, fn, context_lines, dependency_summary_cache)
                symbols_out.append(sym)
                if sym.validation_issues:
                    quality_issues.append(
                        {"module": module_path, "symbol": sym.fqname, "issues": sym.validation_issues}
                    )

            # classes
            for cls in entry.get("classes", []):
                sym = _gen_symbol(cfg, extractor, writer, critic, module_path, cls, context_lines, dependency_summary_cache)
                symbols_out.append(sym)
                if sym.validation_issues:
                    quality_issues.append(
                        {"module": module_path, "symbol": sym.fqname, "issues": sym.validation_issues}
                    )

        # Create ModuleDoc
        module_name = module_path.replace("/", ".").replace("\\", ".")
        if module_name.endswith(".py"):
            module_name = module_name[:-3]

        modules_out.append(
            ModuleDoc(
                module_path=module_path,
                module_name=module_name,
                docstring=module_doc,
                code_hash=module_hash,
                symbols=symbols_out,
            )
        )

    doc_artifacts = DocArtifacts(
        project_key=cfg.project_key,
        repo_root=str(cfg.repo_root),
        model_id=cfg.model_id,
        llm_params=cfg.llm_params_by_role.get("default", cfg.llm_params),
        modules=modules_out,
    )
    write_json(cfg.project_artifacts_dir / "doc_artifacts.json", doc_artifacts.model_dump())

    # Minimal context index (optional)
    write_json(cfg.project_artifacts_dir / "context_index.json", {"project_key": cfg.project_key, "notes": "POC"})

    report = QualityReport(
        project_key=cfg.project_key,
        totals={
            "modules": len(modules_out),
            "symbols": sum(len(m.symbols) for m in modules_out),
            "issues": len(quality_issues),
        },
        issues=quality_issues,
    )
    write_json(cfg.project_artifacts_dir / "quality_report.json", report.model_dump())

    # Optional in-place insertion
    if cfg.insert_docstrings:
        insert_docstrings_inplace_optional(cfg, doc_artifacts)
    
    # Release router resources if using per-agent mode
    if router:
        router.release_role("writer")
        router.release_role("critic")

    return {
        "doc_artifacts_path": str(cfg.project_artifacts_dir / "doc_artifacts.json"),
        "doc_artifacts": doc_artifacts.model_dump(),
    }


def _gen_symbol(cfg, extractor, writer, critic, module_path: str, node: Dict[str, Any], context_lines, dep_cache):
    code_slice, code_hash = extractor.slice_symbol(module_path, node)
    signature = node["symbol"]  # from artifact

    # Build prompt + generate docstring
    prompt = writer.build_prompt(
        kind=("function" if node["kind"] == "function_definition" else "class"),
        module_path=module_path,
        symbol=signature,
        code_slice=code_slice,
        context_lines=context_lines,
    )
    writer_params = cfg.llm_params_by_role.get("writer", cfg.llm_params)
    doc = writer.generate_docstring(prompt=prompt, llm_params=writer_params)
    
    critic_params = cfg.llm_params_by_role.get("critic", cfg.llm_params)
    doc2, issues = critic.review(signature=signature, code_slice=code_slice, docstring=doc, llm_params=critic_params)

    # Save summary for downstream context
    fqname = _fqname(module_path, signature)
    dep_cache[fqname] = one_line_summary(doc2)

    append_jsonl(cfg.cache_dir / "symbol_cache.jsonl", {"fqname": fqname, "code_hash": code_hash, "docstring": doc2})

    return SymbolDoc(
        kind=("function" if node["kind"] == "function_definition" else "class"),
        module_path=module_path,
        name=_symbol_name(signature),
        signature=signature,
        fqname=fqname,
        location=node.get("location"),
        code_hash=code_hash,
        docstring=doc2,
        cached=False,
        validation_issues=issues,
    )


def _symbol_name(signature: str) -> str:
    return signature.split("(", 1)[0].strip()


def _fqname(module_path: str, signature: str) -> str:
    mod = module_path.replace("/", ".").replace("\\", ".")
    if mod.endswith(".py"):
        mod = mod[:-3]
    return f"{mod}.{_symbol_name(signature)}"