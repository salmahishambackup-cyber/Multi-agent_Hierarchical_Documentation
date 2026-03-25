from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from utils.ToolBox.context_tools import build_dependency_context


@dataclass
class ContextAgent:
    max_context_chars: int = 7000

    def build_context_lines(
        self,
        *,
        module_path: str,
        component_hint: str,
        role_hint: str,
        dependency_summary_cache: Dict[str, str],
    ) -> List[str]:
        lines: List[str] = []
        if component_hint:
            lines.append(component_hint)
        if role_hint:
            lines.append(role_hint)

        dep_lines = build_dependency_context(dependency_summary_cache, self.max_context_chars)
        if dep_lines:
            lines.append("Previously generated dependency notes:")
            lines.extend(dep_lines)
        return lines

    def module_role_hint(self, module_path: str) -> str:
        name = module_path.replace("\\", "/")
        if name.endswith("main.py"):
            return "This module appears to be an entrypoint/orchestrator."
        if "data" in name:
            return "This module appears to contain data loading/preprocessing utilities."
        if "classif" in name or "model" in name:
            return "This module appears to contain classification/model utilities."
        return "This module contains project code."

    def component_hint(self, module_path: str, components_json) -> str:
        if not components_json:
            return ""
        for c in components_json.get("data", []):
            if module_path in c.get("files", []):
                return f"Component {c['component_id']}: {c.get('hypothesis','')} (confidence={c.get('confidence')})"
        return ""