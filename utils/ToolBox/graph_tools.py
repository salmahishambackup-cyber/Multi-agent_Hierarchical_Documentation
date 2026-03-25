from __future__ import annotations

from typing import Any, Dict, List

import networkx as nx


def build_module_graph(deps_json: Dict[str, Any]) -> nx.DiGraph:
    g = nx.DiGraph()
    for node in deps_json["data"]["nodes"]:
        if isinstance(node, str) and node.endswith(".py"):
            g.add_node(node)

    for e in deps_json["data"]["edges"]:
        src = e["from"]
        dst = e["to"]
        if isinstance(dst, str) and dst.startswith("internal:"):
            dst_path = dst.split("internal:", 1)[1]
            g.add_edge(src, dst_path)
    return g


def topo_sort_modules(g: nx.DiGraph) -> List[str]:
    if nx.is_directed_acyclic_graph(g):
        return list(nx.topological_sort(g))

    sccs = list(nx.strongly_connected_components(g))
    cg = nx.condensation(g, sccs)
    order = list(nx.topological_sort(cg))
    out: List[str] = []
    for cid in order:
        out.extend(sorted(list(cg.nodes[cid]["members"])))
    return out