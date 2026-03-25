from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from utils.ToolBox.slicing_tools import slice_file_by_bytes
from utils.ToolBox.hashing_tools import sha256_text


@dataclass
class ExtractorAgent:
    repo_root: Path

    def module_stub(self, entry: Dict[str, Any]) -> str:
        imports = [n["symbol"] for n in entry.get("imports", [])]
        fns = [n["symbol"] for n in entry.get("functions", [])]
        clss = [n["symbol"] for n in entry.get("classes", [])]

        lines = []
        if imports:
            lines.append("# Imports:")
            lines.extend([f"- {x}" for x in imports])
        if fns:
            lines.append("# Functions:")
            lines.extend([f"- {x}" for x in fns])
        if clss:
            lines.append("# Classes:")
            lines.extend([f"- {x}" for x in clss])
        return "\n".join(lines).strip()

    def slice_symbol(self, module_path: str, node: Dict[str, Any]) -> Tuple[str, str]:
        """
        Returns (code_slice, code_hash)
        """
        loc = node["location"]
        file_path = self.repo_root / module_path
        sl = slice_file_by_bytes(file_path, loc["start_byte"], loc["end_byte"])
        code_hash = sha256_text(sl.text)
        return sl.text, code_hash