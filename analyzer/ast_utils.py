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

DECORATOR_NODES = {
    "python": {"decorator"},
    "java": {"annotation"},
    "typescript": {"decorator"},
}


# -------------------------------
# Helpers
# -------------------------------
def make_ast_node_id(file_path: str, node) -> str:
    return f"ast:{file_path}:{node.start_byte}:{node.end_byte}"


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


def _extract_docstring(node, source: bytes) -> str | None:
    """Extract docstring from a class or function body (Python-specific)."""
    body = node.child_by_field_name("body")
    if body is None:
        return None
    for child in body.children:
        if child.type == "expression_statement":
            for sub in child.children:
                if sub.type == "string":
                    raw = extract_text(sub, source)
                    if raw:
                        # Strip triple quotes
                        for q in ('"""', "'''"):
                            if raw.startswith(q) and raw.endswith(q):
                                return raw[3:-3].strip()
                        return raw.strip("\"'").strip()
        # First non-comment, non-newline node isn't a string → no docstring
        if child.type not in ("comment", "newline"):
            break
    return None


def _extract_decorators(node, source: bytes, lang: str) -> list[str]:
    """Extract decorator names from a function or class node."""
    decorators = []
    dec_types = DECORATOR_NODES.get(lang, set())
    if not dec_types:
        return decorators
    # Decorators appear as preceding siblings or child nodes
    for child in node.children:
        if child.type in dec_types:
            text = extract_text(child, source)
            if text:
                decorators.append(text)
    return decorators


def _extract_base_classes(node, source: bytes) -> list[str]:
    """Extract base class names from a class node (Python-specific)."""
    bases = []
    superclasses = node.child_by_field_name("superclasses")
    if superclasses is None:
        # Try argument_list (used by Python tree-sitter grammar)
        for child in node.children:
            if child.type == "argument_list":
                superclasses = child
                break
    if superclasses is None:
        return bases
    for child in superclasses.children:
        if child.type not in ("(", ")", ","):
            text = extract_text(child, source)
            if text:
                bases.append(text)
    return bases


def _extract_return_type(node, source: bytes) -> str | None:
    """Extract return type annotation from a function node (Python-specific)."""
    ret = node.child_by_field_name("return_type")
    if ret:
        text = extract_text(ret, source)
        if text and text.startswith("->"):
            return text[2:].strip()
        return text
    return None


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
            entry = {
                "node_id": make_ast_node_id(file_path, node),
                "kind": "class_definition",
                "symbol": name,
                "language": lang,
                "location": {
                    "start_byte": node.start_byte,
                    "end_byte": node.end_byte
                }
            }
            docstring = _extract_docstring(node, source)
            if docstring:
                entry["docstring"] = docstring
            decorators = _extract_decorators(node, source, lang)
            if decorators:
                entry["decorators"] = decorators
            bases = _extract_base_classes(node, source)
            if bases:
                entry["bases"] = bases
            results["classes"].append(entry)

    # -------- FUNCTIONS / METHODS --------
    if node_type in FUNCTION_NODES.get(lang, set()):
        name_node = node.child_by_field_name("name")
        if name_node and depth in (1, 2):
            sig = extract_function_signature(node, source)
            if sig:
                entry = {
                    "node_id": make_ast_node_id(file_path, node),
                    "kind": "function_definition",
                    "symbol": sig,
                    "language": lang,
                    "location": {
                        "start_byte": node.start_byte,
                        "end_byte": node.end_byte
                    }
                }
                docstring = _extract_docstring(node, source)
                if docstring:
                    entry["docstring"] = docstring
                decorators = _extract_decorators(node, source, lang)
                if decorators:
                    entry["decorators"] = decorators
                ret_type = _extract_return_type(node, source)
                if ret_type:
                    entry["return_type"] = ret_type
                results["functions"].append(entry)

    for child in node.children:
        walk_tree(child, source, results, lang, file_path, depth + 1)

