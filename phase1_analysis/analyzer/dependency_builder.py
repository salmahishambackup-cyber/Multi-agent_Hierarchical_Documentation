from collections import defaultdict
from pathlib import Path

# ---- Runtime knowledge base (given) ----
RUNTIME_MODULES = {
    "python": {
        # Core I/O and system
        "os", "sys", "io", "pathlib", "glob", "subprocess",
        # Data structures and serialization
        "json", "pickle", "dataclasses", "collections", "enum",
        # Type hints and functional programming
        "typing", "functools", "itertools",
        # Async and concurrency
        "asyncio", "threading", "multiprocessing", "queue", "concurrent",
        # String and text processing
        "re", "string", "textwrap", "codecs", "base64", "binascii",
        # Math and random
        "math", "random", "statistics", "decimal",
        # Date and time
        "datetime", "time", "calendar", "zoneinfo",
        # Data compression and encoding
        "zipfile", "tarfile", "gzip", "bz2", "lzma",
        # HTTP and URL handling
        "urllib", "urllib.parse", "urllib.request", "email", "mimetypes",
        # Logging and debugging
        "logging", "logging.handlers", "warnings", "traceback", "pdb",
        # Introspection and utilities
        "inspect", "importlib", "abc", "copy", "pprint", "uuid",
        # Context and resource management
        "contextlib", "atexit", "weakref",
    },
    "javascript": {
        "fs", "path", "http", "https", "crypto", "url", "events",
        "util", "stream", "buffer", "os", "process", "child_process",
        "assert", "module"
    },
    "typescript": {
        "fs", "path", "http", "https", "crypto", "url", "events",
        "util", "stream", "buffer", "os", "process", "child_process",
        "assert", "module"
    },
    "java": {
        "java.lang", "java.util", "java.io", "java.time", "java.nio",
        "java.net", "java.security", "java.math", "java.util.concurrent",
        "java.util.stream", "java.functional", "java.text"
    },
    "c": {
        "stdio", "stdlib", "string", "math", "ctype", "time", "assert",
        "errno", "float", "limits", "locale", "setjmp", "signal", "stdarg",
        "stddef", "stdint", "wchar"
    },
    "cpp": {
        "iostream", "vector", "string", "map", "memory", "algorithm",
        "functional", "utility", "array", "deque", "list", "queue", "set",
        "unordered_map", "unordered_set", "stack", "bitset", "numeric",
        "iomanip", "fstream", "sstream", "cstring", "cmath", "cstdlib",
        "ctime", "cassert"
    },
    "csharp": {
        "System", "System.IO", "System.Collections", "System.Linq",
        "System.Text", "System.Threading", "System.Net", "System.Reflection",
        "System.Diagnostics", "System.Runtime", "System.Collections.Generic",
        "System.ComponentModel", "System.Globalization"
    }
}


# ---- Precompute flattened runtime prefixes ----
_RUNTIME_PREFIXES: set[str] = set()

for modules in RUNTIME_MODULES.values():
    for mod in modules:
        _RUNTIME_PREFIXES.add(mod)
def is_language_runtime(name: str) -> bool:
    """
    Check whether a dependency belongs to ANY language runtime
    using the provided multi-language runtime list.

    Works for:
    - exact matches: json, fs
    - namespace matches: java.util.List, System.IO.File
    """

    if not name:
        return False

    # Normalize separators
    normalized = name.replace("\\", ".").replace("/", ".")

    for runtime_prefix in _RUNTIME_PREFIXES:
        if (
            normalized == runtime_prefix
            or normalized.startswith(runtime_prefix + ".")
        ):
            return True

    return False

def extract_cross_language_calls(ast_summaries: list[dict], dependency_graph: dict) -> list[dict]:
    """
    Extract high-level cross-language call patterns for architectural analysis.
    
    Returns list of cross-language edge clusters:
    {
        "from_language": str,
        "to_language": str,
        "call_count": int,
        "examples": [{from, to, evidence}]
    }
    """
    from collections import defaultdict
    
    cross_lang_calls = defaultdict(lambda: {"count": 0, "examples": []})
    
    for edge in dependency_graph.get("edges", []):
        if edge.get("kind") != "cross_language":
            continue
        
        from_lang = edge.get("from_language", "unknown")
        to_lang = edge.get("to_language", "unknown")
        lang_pair = (from_lang, to_lang)
        
        cross_lang_calls[lang_pair]["count"] += 1
        if len(cross_lang_calls[lang_pair]["examples"]) < 3:  # Keep first 3 examples
            cross_lang_calls[lang_pair]["examples"].append({
                "from": edge["from"],
                "to": edge["to"],
                "evidence_count": len(edge.get("evidence", {}).get("evidence", []))
            })
    
    return [
        {
            "from_language": from_lang,
            "to_language": to_lang,
            "call_count": stats["count"],
            "examples": stats["examples"]
        }
        for (from_lang, to_lang), stats in sorted(cross_lang_calls.items())
    ]


def detect_dynamic_import_patterns(import_obj: dict, language: str) -> bool:
    """
    Detect dynamic/uncertain import patterns.
    
    Returns True if import looks dynamically resolved (uncertain).
    """
    raw = import_obj.get("symbol", "")
    
    # -------- PYTHON --------
    if language == "python":
        dynamic_patterns = {
            "__import__(",
            "importlib.import_module",
            "exec(",
            "eval(",
            "getattr(",
            "__getattr__(",
            "load_module",
            "importlib.reload"
        }
        return any(pattern in raw for pattern in dynamic_patterns)
    
    # -------- JAVASCRIPT / TYPESCRIPT --------
    elif language in {"javascript", "typescript"}:
        dynamic_patterns = {
            "import(",  # Dynamic import
            "require.context",
            "require.resolve",
            "__webpack",
            "System.import",
            "eval(",
            "Function("
        }
        return any(pattern in raw for pattern in dynamic_patterns)
    
    # -------- JAVA --------
    elif language == "java":
        dynamic_patterns = {
            "Class.forName",
            "ClassLoader",
            "getClass().forName",
            "ServiceLoader",
            "ReflectionFactory"
        }
        return any(pattern in raw for pattern in dynamic_patterns)
    
    # -------- C / C++ --------
    elif language in {"c", "cpp"}:
        dynamic_patterns = {
            "dlopen(",
            "LoadLibraryA(",
            "GetProcAddress(",
            "#ifdef",
            "#if defined"
        }
        return any(pattern in raw for pattern in dynamic_patterns)
    
    # -------- C# --------
    elif language == "csharp":
        dynamic_patterns = {
            "Assembly.Load",
            "Activator.CreateInstance",
            "Type.GetType",
            "Reflection"
        }
        return any(pattern in raw for pattern in dynamic_patterns)
    
    return False

def normalize_import(import_obj) -> dict | None:
    """
    Normalize an import AST object into a semantic dependency.
    Output is language-agnostic and architecture-aware.
    Preserves complete evidence for traceability and validation.
    Detects dynamic/uncertain imports and marks appropriately.
    """

    # -------- Extract raw import text and evidence --------
    if isinstance(import_obj, dict):
        raw = import_obj.get("symbol")
        node_id = import_obj.get("node_id")
        language = import_obj.get("language")
        kind = import_obj.get("kind", "import")
        location = import_obj.get("location", {})
    else:
        raw = str(import_obj)
        node_id = None
        language = None
        kind = "import"
        location = {}

    if not raw:
        return None

    raw = raw.strip()

    # -------- DYNAMIC IMPORT DETECTION --------
    is_dynamic = detect_dynamic_import_patterns(import_obj if isinstance(import_obj, dict) else {}, language or "")

    module = None

    # -------- PYTHON --------
    if language == "python":
        if raw.startswith("import "):
            # import os, sys
            module = raw.replace("import ", "").split(",")[0].strip()

        elif raw.startswith("from "):
            # from api.config import load_config
            parts = raw.split()
            if len(parts) >= 4:
                module = parts[1]
        
        elif "__import__" in raw or "importlib" in raw:
            # __import__('module_name')
            # importlib.import_module('module_name')
            import re as regex
            match = regex.search(r"['\"]([^'\"]+)['\"]", raw)
            if match:
                module = match.group(1)

    # -------- JAVASCRIPT / TYPESCRIPT --------
    elif language in {"javascript", "typescript"}:
        # import { x } from "next/server"
        # import x from "lodash"
        # import("lodash")
        if "from" in raw:
            module = raw.split("from")[-1].strip().strip(";").strip("'\"")
        else:
            # require("fs") or import("fs")
            if "(" in raw and ")" in raw:
                module = raw.split("(")[-1].split(")")[0].strip("'\"")

    # -------- C / C++ --------
    elif language in {"c", "cpp"}:
        if raw.startswith("#include"):
            if "<" in raw:
                module = raw.split("<")[1].split(">")[0]
            elif '"' in raw:
                module = raw.split('"')[1]
        elif "dlopen" in raw:
            # dlopen("libc.so.6", RTLD_NOW)
            import re as regex
            match = regex.search(r"['\"]([^'\"]+)['\"]", raw)
            if match:
                module = match.group(1)

    # -------- JAVA / C# --------
    elif language in {"java", "csharp"}:
        if raw.startswith("import"):
            module = raw.replace("import", "").replace(";", "").strip()
        elif "Class.forName" in raw or "Type.GetType" in raw:
            # Class.forName("java.lang.String")
            import re as regex
            match = regex.search(r"['\"]([^'\"]+)['\"]", raw)
            if match:
                module = match.group(1)

    if not module:
        return None

    # -------- CLASSIFICATION --------

    # Dynamic imports get marked with lower confidence
    if is_dynamic:
        dep_kind = "uncertain_dynamic"
    # Runtime / standard library
    elif is_language_runtime(module):
        dep_kind = "language_runtime"
    # Internal module (repo-level decision later)
    elif "." in module or "/" in module:
        dep_kind = "unknown_internal_or_external"
    else:
        dep_kind = "external_library"

    # -------- EVIDENCE STRUCTURE --------
    evidence = {
        "node_id": node_id,
        "symbol": raw,
        "kind": kind,
        "location": location,
        "language": language,
        "is_dynamic": is_dynamic
    }

    return {
        "name": module,
        "kind": dep_kind,
        "language": language,
        "evidence": evidence
    }

def extract_file_dependencies(ast_summaries: list[dict], repo_root: str) -> list[dict]:
    """
    Extract semantic dependencies from AST, including dynamic imports and cross-language.
    
    Assumes ast_summaries contain already-normalized repo-relative POSIX paths.
    
    Edge kinds:
    - internal_module: File imports another file in same repo
    - cross_language: Reference crosses language boundary
    - uncertain_dynamic: Dynamically resolved import
    - external_library: Third-party package import
    - language_runtime: Standard library or built-in module
    """
    edges = []
    
    # Build internal module index using normalized paths from AST
    internal_index = {}
    file_language_map = {}
    
    for entry in ast_summaries:
        # AST entries already have normalized repo-relative POSIX paths
        src_file = entry["file"]
        src_language = entry.get("language", "unknown")
        
        file_language_map[src_file] = src_language
        
        # Build multiple module name variants for flexible matching
        # api/config.py → ["api.config", "config"]
        # src/app/api/auth/status/route.ts → ["src.app.api.auth.status.route", "status.route", "route"]
        parts = Path(src_file).with_suffix("").parts
        
        # Add full dotted path
        if len(parts) > 0:
            internal_index[".".join(parts)] = src_file
        
        # Add progressively shorter suffixes (last 2, last 1)
        if len(parts) >= 2:
            internal_index[".".join(parts[-2:])] = src_file
        if len(parts) >= 1:
            internal_index[parts[-1]] = src_file


    # Extract dependencies
    for entry in ast_summaries:
        src_file = entry["file"]  # Already normalized
        src_language = entry.get("language", "unknown")

        for imp in entry.get("imports", []):
            dep = normalize_import(imp)
            if not dep:
                continue

            module = dep["name"]
            evidence = dep.get("evidence", {})
            dep_kind = dep.get("kind")

            edge = None

            # -------- UNCERTAIN DYNAMIC --------
            if dep_kind == "uncertain_dynamic":
                edge = {
                    "from": src_file,
                    "to": f"dynamic:{module}",
                    "kind": "uncertain_dynamic",
                    "confidence": 0.4,
                    "note": "Dynamically resolved at runtime; static analysis cannot fully determine target",
                    "evidence": evidence
                }

            # -------- INTERNAL (same language) --------
            elif module in internal_index:
                target_file = internal_index[module]
                target_language = file_language_map.get(target_file, "unknown")
                
                # Detect cross-language import
                if src_language != target_language and src_language != "unknown" and target_language != "unknown":
                    edge = {
                        "from": src_file,
                        "to": f"internal:{target_file}",
                        "kind": "cross_language",
                        "from_language": src_language,
                        "to_language": target_language,
                        "evidence": evidence
                    }
                else:
                    edge = {
                        "from": src_file,
                        "to": f"internal:{target_file}",
                        "kind": "internal_module",
                        "evidence": evidence
                    }

            # -------- RUNTIME --------
            elif is_language_runtime(module):
                edge = {
                    "from": src_file,
                    "to": f"runtime:{module}",
                    "kind": "language_runtime",
                    "evidence": evidence
                }

            # -------- EXTERNAL --------
            else:
                edge = {
                    "from": src_file,
                    "to": f"external:{module}",
                    "kind": "external_library",
                    "evidence": evidence
                }

            if edge:
                edges.append(edge)

    # Sort by (from, to) for determinism
    return sorted(edges, key=lambda e: (e["from"], e["to"]))



def build_dependency_graph(ast_summaries: list[dict], repo_root: str) -> dict:
    edges = extract_file_dependencies(ast_summaries, repo_root)

    # Start with all files from AST as nodes (including those with no dependencies)
    nodes = set()
    for summary in ast_summaries:
        file_path = summary.get("file")
        if file_path:
            nodes.add(file_path)
    
    # Add all edge sources and targets (to catch external dependencies)
    for e in edges:
        nodes.add(e["from"])
        nodes.add(e["to"])

    return {
        "nodes": sorted(nodes),
        "edges": edges
    }
