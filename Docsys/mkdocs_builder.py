from __future__ import annotations

import warnings
import subprocess
from pathlib import Path
from typing import Optional


# DEPRECATED: This module is kept for backward compatibility only.
# MkDocs HTML generation is no longer the recommended output format.
warnings.warn(
    "mkdocs_builder is deprecated and will be removed in a future version. "
    "Use the new README generation instead for cleaner documentation.",
    DeprecationWarning,
    stacklevel=2,
)


def mkdocs_build_optional(cfg, mkdocs_root: str) -> Optional[str]:
    """
    Runs `mkdocs build` in the per-project artifacts directory.
    Produces `site/` under Artifacts/<project_key>/site/
    """
    project_dir = cfg.project_artifacts_dir
    try:
        subprocess.check_call(["mkdocs", "build", "-f", str(project_dir / "mkdocs.yml")], cwd=str(project_dir))
        site_dir = project_dir / "site"
        if cfg.debug:
            print(f"[MkDocs] Built static HTML at: {site_dir}")
        return str(site_dir)
    except FileNotFoundError:
        if cfg.debug:
            print("[MkDocs] mkdocs not installed; skipping HTML build.")
        return None