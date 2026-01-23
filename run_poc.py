import os

# Reduce HF/Transformers download and warning noise
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import argparse
import json
from pathlib import Path

from docsys.artifacts import load_ast_artifact, load_deps_artifact, load_components_artifact
from docsys.graph import build_module_graph, topo_sort_modules
from docsys.generator import DocstringPOC, GenerationConfig


def main():
    ap = argparse.ArgumentParser(description="Artifact-driven docstring generation POC")
    ap.add_argument("--repo_root", required=True, help="Path to repository root containing source files.")
    ap.add_argument("--ast_json", required=True)
    ap.add_argument("--deps_json", required=True)
    ap.add_argument("--components_json", required=False)

    ap.add_argument("--model_id", required=True, help="HF model id, e.g., Qwen/Qwen2.5-Coder-7B-Instruct")
    ap.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda", "mps"])
    ap.add_argument("--dtype", default="auto", choices=["auto", "float16", "bfloat16", "float32"])
    ap.add_argument("--max_new_tokens", type=int, default=240)
    ap.add_argument("--temperature", type=float, default=0.2)
    ap.add_argument("--top_p", type=float, default=0.95)

    ap.add_argument("--max_context_chars", type=int, default=7000)
    ap.add_argument("--out", default="generated_docstrings.json")

    # NEW: streaming / incremental save
    ap.add_argument("--stream", action="store_true", help="Print docstrings as they are generated.")
    ap.add_argument("--save_every_module", action="store_true", help="Save partial JSON after each module.")
    ap.add_argument("--partial_out", default="generated_docstrings.partial.json")

    args = ap.parse_args()

    repo_root = Path(args.repo_root).resolve()
    ast_art = load_ast_artifact(Path(args.ast_json))
    deps_art = load_deps_artifact(Path(args.deps_json))
    comps_art = load_components_artifact(Path(args.components_json)) if args.components_json else None

    graph = build_module_graph(deps_art)
    module_order = topo_sort_modules(graph)

    cfg = GenerationConfig(
        model_id=args.model_id,
        device=args.device,
        dtype=args.dtype,
        max_new_tokens=args.max_new_tokens,
        temperature=args.temperature,
        top_p=args.top_p,
        max_context_chars=args.max_context_chars,
    )

    poc = DocstringPOC(
        repo_root=repo_root,
        ast_artifact=ast_art,
        deps_artifact=deps_art,
        components_artifact=comps_art,
        module_order=module_order,
        config=cfg,
        stream=args.stream,
        save_every_module=args.save_every_module,
        partial_out=Path(args.partial_out),
    )

    results = poc.run()

    Path(args.out).write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"\nWrote: {args.out}")


if __name__ == "__main__":
    main()