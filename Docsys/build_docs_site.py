from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any, Dict

from jinja2 import Environment, FileSystemLoader

from Utils.ToolBox.io_tools import ensure_dir, write_json, read_json
from Utils.ToolBox.artifact_loader import load_project_artifacts


# DEPRECATED: This module is kept for backward compatibility only.
# Use the new build_readme.py for cleaner artifact-driven documentation.
warnings.warn(
    "build_docs_site is deprecated and will be removed in a future version. "
    "Use build_readme.py instead for artifact-driven documentation.",
    DeprecationWarning,
    stacklevel=2,
)


def build_docs_site(cfg, stage_a: Dict[str, Any]) -> Dict[str, Any]:
    """
    Stage B (no-import mode):
      doc_artifacts.json + analyzer artifacts -> docs/ markdown site + mkdocs.yml
    """
    project_dir = cfg.project_artifacts_dir
    doc_artifacts = read_json(project_dir / "doc_artifacts.json")

    analyzer = load_project_artifacts(project_dir)
    deps_json = analyzer["deps"]
    components_json = analyzer["components"]

    mkdocs_root = project_dir / "docs"
    ensure_dir(mkdocs_root)
    ensure_dir(mkdocs_root / "architecture")
    ensure_dir(mkdocs_root / "api")

    # Load templates
    env = Environment(
        loader=FileSystemLoader(str(Path("Utils/Doc_template/mkdocs"))),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )

    # Build nav entries dynamically from modules in doc_artifacts
    modules = doc_artifacts["modules"]
    nav_api = []
    for m in modules:
        nav_api.append({"title": m["module_name"], "path": f"api/{m['module_name']}.md"})

    # Render mkdocs.yml
    mkdocs_yml = env.get_template("mkdocs.yml.j2").render(
        site_name=f"{cfg.project_key} Documentation",
        nav_api=nav_api,
    )
    (project_dir / "mkdocs.yml").write_text(mkdocs_yml, encoding="utf-8")

    # Render pages
    (mkdocs_root / "index.md").write_text(
        env.get_template("index.md.j2").render(project_key=cfg.project_key, doc_artifacts=doc_artifacts),
        encoding="utf-8",
    )
    (mkdocs_root / "getting-started.md").write_text(
        env.get_template("getting-started.md.j2").render(project_key=cfg.project_key, doc_artifacts=doc_artifacts),
        encoding="utf-8",
    )

    (mkdocs_root / "architecture" / "overview.md").write_text(
        env.get_template("architecture_overview.md.j2").render(
            project_key=cfg.project_key,
            components=components_json,
        ),
        encoding="utf-8",
    )
    (mkdocs_root / "architecture" / "dependencies.md").write_text(
        env.get_template("dependencies.md.j2").render(
            project_key=cfg.project_key,
            deps=deps_json,
        ),
        encoding="utf-8",
    )

    # API pages (no-import mode): embed docstrings from doc_artifacts
    api_tmpl = env.get_template("api_module.md.j2")
    for m in modules:
        out = api_tmpl.render(module=m)
        (mkdocs_root / "api" / f"{m['module_name']}.md").write_text(out, encoding="utf-8")

    if cfg.debug:
        print(f"[Stage B] MkDocs markdown generated at: {mkdocs_root}")
        print(f"[Stage B] mkdocs.yml generated at: {project_dir / 'mkdocs.yml'}")

    return {"mkdocs_root": str(mkdocs_root), "mkdocs_yml": str(project_dir / "mkdocs.yml")}