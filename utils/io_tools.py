"""
File I/O utilities for the documentation pipeline.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any


def ensure_dir(p: Path | str) -> None:
    """Create directory if it doesn't exist."""
    Path(p).mkdir(parents=True, exist_ok=True)


def write_json(path: Path | str, data: Any) -> None:
    """Write data to JSON file."""
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def read_json(path: Path | str) -> Any:
    """Read data from JSON file."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def append_jsonl(path: Path | str, obj: Any) -> None:
    """Append object to JSONL file."""
    with Path(path).open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def rm_tree_safe(path: Path | str) -> None:
    """Safely remove directory tree."""
    p = Path(path)
    if p.exists():
        shutil.rmtree(p)


def project_key_from_repo_root(repo_root: Path | str) -> str:
    """Generate project key from repository root path."""
    return Path(repo_root).name
