from __future__ import annotations

from typing import Dict, List


def one_line_summary(docstring: str) -> str:
    for line in docstring.splitlines():
        s = line.strip()
        if s:
            return s
    return ""


def trim_lines_to_chars(lines: List[str], max_chars: int) -> List[str]:
    out: List[str] = []
    used = 0
    for ln in lines:
        if used + len(ln) > max_chars:
            break
        out.append(ln)
        used += len(ln)
    return out


def build_dependency_context(
    dependency_summary_cache: Dict[str, str],
    max_chars: int,
) -> List[str]:
    lines = []
    for k, v in dependency_summary_cache.items():
        lines.append(f"- {k}: {v}")
    return trim_lines_to_chars(lines, max_chars)