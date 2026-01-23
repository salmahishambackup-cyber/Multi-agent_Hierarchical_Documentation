from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from Utils.ToolBox.io_tools import read_json


def load_project_artifacts(project_artifacts_dir: Path) -> Dict[str, Any]:
    """
    Loads analyzer-provided artifacts from Artifacts/<project_key>/.
    """
    return {
        "ast": read_json(project_artifacts_dir / "ast.json"),
        "deps": read_json(project_artifacts_dir / "dependencies_normalized.json"),
        "components": read_json(project_artifacts_dir / "components.json"),
    }