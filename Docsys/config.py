from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict


@dataclass
class PipelineConfig:
    repo_root: Path
    project_key: str
    project_artifacts_dir: Path
    cache_dir: Path

    model_id: str
    device: str = "auto"
    dtype: str = "auto"

    llm_params: Dict[str, Any] = field(default_factory=dict)
    insert_docstrings: bool = False
    debug: bool = True

    # Artifact filenames (input)
    ast_file: str = "ast.json"
    deps_file: str = "dependencies_normalized.json"
    components_file: str = "components.json"