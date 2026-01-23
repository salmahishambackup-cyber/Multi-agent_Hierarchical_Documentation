from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def append_jsonl(path: Path, obj: Any) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def rm_tree_safe(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def project_key_from_repo_root(repo_root: Path) -> str:
    return repo_root.name