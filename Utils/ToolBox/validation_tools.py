from __future__ import annotations

import re
from typing import List, Tuple


def extract_params_from_signature(signature: str) -> List[str]:
    m = re.search(r"\((.*)\)", signature)
    if not m:
        return []
    inside = m.group(1).strip()
    if not inside:
        return []
    parts = [p.strip() for p in inside.split(",")]
    names = []
    for p in parts:
        p = p.split("=", 1)[0].strip()
        p = p.split(":", 1)[0].strip()
        if p in ("*", "/", "**"):
            continue
        p = p.lstrip("*")
        if p:
            names.append(p)
    return names


def validate_google_docstring(doc: str, signature: str) -> List[str]:
    """
    Returns list of issues (empty if OK).
    """
    issues: List[str] = []
    params = extract_params_from_signature(signature)
    if params:
        if "Args:" not in doc:
            issues.append("Missing 'Args:' section for callable with parameters.")
        else:
            for p in params:
                if re.search(rf"^\s*{re.escape(p)}\s*:", doc, flags=re.MULTILINE) is None:
                    issues.append(f"Parameter '{p}' not documented under Args.")
    return issues