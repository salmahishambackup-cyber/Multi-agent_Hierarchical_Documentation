from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from Utils.ToolBox.io_tools import read_json
from Utils.ToolBox.llm_clients.hf_client import HFClient


@dataclass
class WriterAgent:
    hf: HFClient
    google_prompt_path: Path

    def build_prompt(self, *, kind: str, module_path: str, symbol: str, code_slice: str, context_lines: List[str]) -> str:
        rules = self.google_prompt_path.read_text(encoding="utf-8").strip()

        context_block = "\n".join([ln for ln in context_lines if ln.strip()]).strip()
        if context_block:
            context_block = (
                "\nContext (may be incomplete, use only if consistent with code):\n"
                f"{context_block}\n"
            )

        return "\n".join(
            [
                rules,
                "",
                "Target:",
                f"- kind: {kind}",
                f"- module: {module_path}",
                f"- symbol: {symbol}",
                "",
                context_block.rstrip(),
                "Code slice:",
                "```python",
                code_slice.rstrip(),
                "```",
                "",
                "Task:",
                "Write ONLY the docstring content (do not include surrounding quotes). "
                "Use Google format. Include sections only if applicable.",
                "",
            ]
        ).strip()

    def generate_docstring(self, *, prompt: str, llm_params: Dict[str, Any]) -> str:
        out = self.hf.generate(prompt, llm_params)
        out = out.strip().strip('"""').strip("'''").strip()
        return out