from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Literal, Optional


DocstringMode = Literal["none", "modules_only", "symbols_and_modules"]


@dataclass
class PipelineConfig:
    repo_root: Path
    project_key: str
    project_artifacts_dir: Path
    cache_dir: Path

    model_id: str
    device: str = "auto"
    dtype: str = "auto"

    # New: per-role LLM params
    llm_params_by_role: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Backward compatibility: single llm_params (falls back to llm_params_by_role["default"])
    @property
    def llm_params(self) -> Dict[str, Any]:
        """Backward-compatible accessor for llm_params."""
        return self.llm_params_by_role.get("default", {})
    
    @llm_params.setter
    def llm_params(self, value: Dict[str, Any]) -> None:
        """Backward-compatible setter for llm_params."""
        self.llm_params_by_role["default"] = value
    
    # Docstring generation mode
    docstring_mode: DocstringMode = "modules_only"
    
    insert_docstrings: bool = False
    debug: bool = True

    # Artifact filenames (input)
    ast_file: str = "ast.json"
    deps_file: str = "dependencies_normalized.json"
    components_file: str = "components.json"