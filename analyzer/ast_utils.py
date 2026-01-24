# analysis/ast_utils.py

# -------------------------------
# Node type maps per language
# -------------------------------

IMPORT_NODES = {
    "python": {"import_statement", "import_from_statement"},
    "java": {"import_declaration"},
    "javascript": {"import_statement"},
    "typescript": {"import_statement"},
    "c": {"preproc_include"},
    "cpp": {"preproc_include"},
    "csharp": {"using_directive"},
}

CLASS_NODES = {
    "python": {"class_definition"},
    "java": {"class_declaration", "interface_declaration"},
    "javascript": {"class_declaration"},
    "typescript": {"class_declaration", "interface_declaration"},
    "c": {"struct_specifier"},
    "cpp": {"class_specifier", "struct_specifier"},
    "csharp": {"class_declaration", "struct_declaration", "interface_declaration"},
}

FUNCTION_NODES = {
    "python": {"function_definition"},
    "java": {"method_declaration"},
    "javascript": {"function_declaration"},
    "typescript": {"function_declaration"},
    "c": {"function_definition"},
    "cpp": {"function_definition"},
    "csharp": {"method_declaration"},
}


# -------------------------------
# Helpers
# -------------------------------
def make_ast_node_id(file_path: str, node) -> str:
    return f"ast:{file_path}:{node.start_byte}:{node.end_byte}"
0
def extract_text(node, source: bytes) -> str | None:
    try:
        return source[node.start_byte:node.end_byte].decode(
            "utf-8", errors="ignore"
        ).strip()
    except Exception:
        return None


def extract_name(node, source: bytes) -> str | None:
    name_node = node.child_by_field_name("name")
    if not name_node:
        return None

    return source[name_node.start_byte:name_node.end_byte].decode(
        "utf-8", errors="ignore"
    ).strip()


def extract_function_signature(node, source: bytes) -> str | None:
    name_node = node.child_by_field_name("name")
    if not name_node:
        return None  # anonymous / lambda

    name = source[name_node.start_byte:name_node.end_byte].decode(
        "utf-8", errors="ignore"
    ).strip()

    params_node = (
        node.child_by_field_name("parameters")
        or node.child_by_field_name("parameter_list")
    )

    params = ""
    if params_node:
        params = source[
            params_node.start_byte:params_node.end_byte
        ].decode("utf-8", errors="ignore").strip()

    return f"{name}{params}"


# -------------------------------
# Main AST walker
# -------------------------------

def walk_tree(node, source, results, lang, file_path, depth=0):
    node_type = node.type

    # Hard depth cutoff (prevents deep noise)
    if depth > 3:
        return

    # -------- IMPORTS --------
    if node_type in IMPORT_NODES.get(lang, set()) and depth <= 1:
        text = extract_text(node, source)
        if text:
            # ---- JS / TS ----
            if lang in {"javascript", "typescript"} and "from" in text:
                symbol = text.split("from")[-1].strip().strip(";").strip("'\"")
            else:
                symbol = text

            results["imports"].append({
                "node_id": make_ast_node_id(file_path, node),
                "kind": "import",
                "symbol": symbol,
                "language": lang,
                "location": {
                    "start_byte": node.start_byte,
                    "end_byte": node.end_byte
                }
            })

    # -------- CLASSES / STRUCTS --------
    if node_type in CLASS_NODES.get(lang, set()) and depth == 1:
        name = extract_name(node, source)
        if name:
            results["classes"].append({
                "node_id": make_ast_node_id(file_path, node),
                "kind": "class_definition",
                "symbol": name,
                "language": lang,
                "location": {
                    "start_byte": node.start_byte,
                    "end_byte": node.end_byte
                }
            })

    # -------- FUNCTIONS / METHODS --------
    if node_type in FUNCTION_NODES.get(lang, set()):
        name_node = node.child_by_field_name("name")
        if name_node and depth in (1, 2):
            sig = extract_function_signature(node, source)
            if sig:
                results["functions"].append({
                    "node_id": make_ast_node_id(file_path, node),
                    "kind": "function_definition",
                    "symbol": sig,
                    "language": lang,
                    "location": {
                        "start_byte": node.start_byte,
                        "end_byte": node.end_byte
                    }
                })

    for child in node.children:
        walk_tree(child, source, results, lang, file_path, depth + 1)

