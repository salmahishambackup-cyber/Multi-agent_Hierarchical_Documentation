import os
from utils.id_generator import generate_id
from utils.path_utils import normalize_path


# =========================
# Configuration heuristics
# =========================

CONFIG_FILES = {
    "package.json",
    "package-lock.json",
    "tsconfig.json",
    "tailwind.config.js",
    "vite.config.js"
}


# =========================
# Main structure builder
# =========================

def build_structure(repo_name: str, files: list[str], max_depth: int = 3) -> dict:
    tree = {}

    # 1️⃣ Build directory tree
    for file_path in files:
        path = normalize_path(file_path)
        filename = os.path.basename(path)

        # --- NEW PART (هنا بالظبط) ---
        if filename in CONFIG_FILES:
            tree.setdefault("config", {}).setdefault("__files__", []).append(path)
            continue
        # --- END NEW PART ---

        parts = path.split("/")
        node = tree

        for depth, part in enumerate(parts[:-1]):
            if depth >= max_depth:
                break
            node = node.setdefault(part, {})

        node.setdefault("__files__", []).append(path)

    # 2️⃣ Convert tree to module schema
    module_counter = 1

    def describe_module(name: str) -> str:
        if name in {"api", "backend"}:
            return "Backend service layer"
        if name in {"src", "app"}:
            return "Frontend application"
        if name in {"tests", "test"}:
            return "Test suite"
        if name == "config":
            return "Configuration and tooling"
        return f"{name} module"

    def build_module(name, subtree):
        nonlocal module_counter
        module_id = generate_id("MOD", module_counter)
        module_counter += 1

        files = subtree.get("__files__", [])
        children = []

        for key, value in subtree.items():
            if key == "__files__":
                continue
            children.append(build_module(key, value))

        return {
            "module_id": module_id,
            "name": name,
            "description": describe_module(name),
            "files": files,
            "children": children
        }

    root_files = tree.get("__files__", [])
    root_children = []

    for key, value in tree.items():
        if key != "__files__":
            root_children.append(build_module(key, value))

    return {
        "repo": {"name": repo_name},
        "root_module": {
            "module_id": generate_id("MOD", 0),
            "name": "root",
            "description": "Top-level repository module",
            "files": root_files,
            "children": root_children
        }
    }
