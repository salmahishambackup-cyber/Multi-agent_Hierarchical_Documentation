from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

from utils.ToolBox.validation_tools import validate_google_docstring
from utils.ToolBox.llm_clients.hf_client import HFClient


@dataclass
class CriticAgent:
    hf: HFClient
    critic_prompt_path: Path

    def review(
        self,
        *,
        signature: str,
        code_slice: str,
        docstring: str,
        llm_params: Dict[str, Any],
    ) -> Tuple[str, List[str]]:
        """
        Returns (final_docstring, issues)
        POC: do static validation; if issues exist, ask LLM to revise once.
        """
        issues = validate_google_docstring(docstring, signature)
        if not issues:
            return docstring, []

        rules = self.critic_prompt_path.read_text(encoding="utf-8").strip()
        prompt = "\n".join(
            [
                rules,
                "",
                f"Signature: {signature}",
                "",
                "Code slice:",
                "```python",
                code_slice.rstrip(),
                "```",
                "",
                "Docstring to review:",
                "```text",
                docstring.rstrip(),
                "```",
                "",
                f"Issues detected: {issues}",
                "",
                "Return either:",
                "- APPROVED (if you think it's fine), or",
                "- REVISE + corrected docstring content only.",
            ]
        )

        revised = self.hf.generate(prompt, llm_params).strip()

        if revised.startswith("APPROVED"):
            return docstring, issues

        if revised.startswith("REVISE"):
            # everything after REVISE line
            parts = revised.splitlines()
            revised_doc = "\n".join(parts[1:]).strip().strip('"""').strip("'''").strip()
            # re-check
            issues2 = validate_google_docstring(revised_doc, signature)
            return revised_doc, issues2

        # fallback: keep original but report issues
        return docstring, issues