from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from Docsys.schemas import DocPlan, PlanTask
from Utils.ToolBox.graph_tools import build_module_graph, topo_sort_modules


@dataclass
class PlannerAgent:
    def build_plan(self, *, project_key: str, ast_json: Dict[str, Any], deps_json: Dict[str, Any]) -> DocPlan:
        g = build_module_graph(deps_json)
        module_order = topo_sort_modules(g)

        # Index AST by file
        ast_entries = {e["file"]: e for e in ast_json["data"]}

        tasks: List[PlanTask] = []
        tid = 0

        for module_path in module_order:
            entry = ast_entries.get(module_path)
            if not entry:
                continue

            # module docstring task
            tid += 1
            tasks.append(PlanTask(task_id=f"t{tid}", module_path=module_path, kind="module"))

            # functions
            for fn in entry.get("functions", []):
                tid += 1
                tasks.append(
                    PlanTask(
                        task_id=f"t{tid}",
                        module_path=module_path,
                        kind="function",
                        symbol=fn["symbol"],
                        node_id=fn.get("node_id"),
                    )
                )

            # classes
            for cls in entry.get("classes", []):
                tid += 1
                tasks.append(
                    PlanTask(
                        task_id=f"t{tid}",
                        module_path=module_path,
                        kind="class",
                        symbol=cls["symbol"],
                        node_id=cls.get("node_id"),
                    )
                )

        return DocPlan(project_key=project_key, module_order=module_order, tasks=tasks)