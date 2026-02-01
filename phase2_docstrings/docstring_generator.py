"""
Phase 2: Docstring generation using lightweight LLM.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List, Optional
import networkx as nx

from phase2_docstrings.agents import Writer
from utils import get_cache_key, load_from_cache, save_to_cache, write_json
from utils.profiler import profile_phase


class DocstringGenerator:
    """
    Phase 2: Generate Google-style docstrings for modules, functions, and classes.
    Uses caching and topological ordering for efficiency.
    """
    
    def __init__(
        self,
        writer: Writer,
        repo_path: str,
        artifacts_dir: str,
        cache_dir: str,
        ast_data: Dict[str, Any],
        deps_data: Dict[str, Any],
    ):
        """
        Initialize docstring generator.
        
        Args:
            writer: Writer agent for LLM generation
            repo_path: Path to repository
            artifacts_dir: Directory for artifacts
            cache_dir: Directory for caching results
            ast_data: AST artifact data
            deps_data: Dependencies artifact data
        """
        self.writer = writer
        self.repo_path = Path(repo_path).resolve()
        self.artifacts_dir = Path(artifacts_dir).resolve()
        self.cache_dir = Path(cache_dir).resolve()
        self.ast_data = ast_data
        self.deps_data = deps_data
    
    @profile_phase("Phase 2: Docstrings")
    def run(self) -> Dict[str, Any]:
        """
        Generate docstrings for all modules.
        
        Returns:
            Dictionary with generated docstrings and stats
        """
        # Build topological order
        module_order = self._get_module_order()
        
        results = {}
        cached_count = 0
        generated_count = 0
        
        print(f"Processing {len(module_order)} modules...")
        
        for module_path in module_order:
            if module_path not in self.ast_data:
                continue
            
            module_info = self.ast_data[module_path]
            
            # Generate module docstring
            module_doc = self._generate_module_docstring(module_path, module_info)
            
            if module_doc.get("cached"):
                cached_count += 1
            else:
                generated_count += 1
            
            # Generate docstrings for functions and classes
            functions_docs = []
            for func in module_info.get("functions", []):
                func_doc = self._generate_function_docstring(module_path, func)
                functions_docs.append(func_doc)
                if func_doc.get("cached"):
                    cached_count += 1
                else:
                    generated_count += 1
            
            classes_docs = []
            for cls in module_info.get("classes", []):
                cls_doc = self._generate_class_docstring(module_path, cls)
                classes_docs.append(cls_doc)
                if cls_doc.get("cached"):
                    cached_count += 1
                else:
                    generated_count += 1
            
            results[module_path] = {
                "module_docstring": module_doc,
                "functions": functions_docs,
                "classes": classes_docs,
            }
        
        # Save results
        output_path = self.artifacts_dir / "doc_artifacts.json"
        write_json(output_path, results)
        
        total = cached_count + generated_count
        print(f"✅ {total} docstrings generated ({cached_count} cached, {generated_count} new)")
        
        return {
            "output_path": str(output_path),
            "stats": {
                "total": total,
                "cached": cached_count,
                "generated": generated_count,
            },
            "docstrings": results,
        }
    
    def _get_module_order(self) -> List[str]:
        """Get modules in topological order (dependencies first)."""
        graph = nx.DiGraph()
        
        # Add all modules
        for module in self.ast_data.keys():
            graph.add_node(module)
        
        # Add edges from dependencies
        for module, deps in self.deps_data.get("internal_dependencies", {}).items():
            for dep in deps:
                if dep in self.ast_data:
                    graph.add_edge(dep, module)
        
        # Return topological order (or just keys if cyclic)
        try:
            return list(nx.topological_sort(graph))
        except nx.NetworkXError:
            return list(self.ast_data.keys())
    
    def _generate_module_docstring(self, module_path: str, module_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate docstring for a module."""
        # Read module content
        full_path = self.repo_path / module_path
        try:
            content = full_path.read_text()
        except Exception:
            return {"error": "Could not read file"}
        
        # Check cache
        cache_key = get_cache_key(content[:1000])  # Use first 1000 chars as key
        cached = load_from_cache(self.cache_dir, cache_key, "docstrings")
        
        if cached:
            return {"docstring": cached["docstring"], "cached": True}
        
        # Build context
        context = self._build_context(module_path)
        
        # Get first ~500 chars as representative sample
        code_sample = content[:500]
        
        # Generate docstring
        try:
            docstring = self.writer.generate_docstring(code_sample, context)
            
            result = {"docstring": docstring, "cached": False}
            save_to_cache(self.cache_dir, cache_key, result, "docstrings")
            
            return result
        except Exception as e:
            return {"error": str(e)}
    
    def _generate_function_docstring(self, module_path: str, func_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate docstring for a function."""
        # Read function code using byte positions
        full_path = self.repo_path / module_path
        try:
            content = full_path.read_bytes()
            start = func_info.get("start_byte", 0)
            end = func_info.get("end_byte", len(content))
            
            # Limit extraction to reasonable size (10KB max)
            MAX_CODE_SIZE = 10000
            if end - start > MAX_CODE_SIZE:
                end = start + MAX_CODE_SIZE
            
            code = content[start:end].decode("utf-8", errors="ignore")
        except Exception:
            return {"name": func_info.get("name", "unknown"), "error": "Could not read function"}
        
        # Check cache
        cache_key = get_cache_key(code)
        cached = load_from_cache(self.cache_dir, cache_key, "docstrings")
        
        if cached:
            return {
                "name": func_info.get("name", "unknown"),
                "docstring": cached["docstring"],
                "cached": True,
            }
        
        # Build context
        context = self._build_context(module_path)
        
        # Generate docstring
        try:
            docstring = self.writer.generate_docstring(code, context)
            
            result = {"docstring": docstring}
            save_to_cache(self.cache_dir, cache_key, result, "docstrings")
            
            return {
                "name": func_info.get("name", "unknown"),
                "docstring": docstring,
                "cached": False,
            }
        except Exception as e:
            return {"name": func_info.get("name", "unknown"), "error": str(e)}
    
    def _generate_class_docstring(self, module_path: str, class_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate docstring for a class."""
        # Similar to function but for class
        full_path = self.repo_path / module_path
        try:
            content = full_path.read_bytes()
            start = class_info.get("start_byte", 0)
            end = class_info.get("end_byte", len(content))
            
            # Limit extraction to reasonable size (10KB max)
            MAX_CODE_SIZE = 10000
            if end - start > MAX_CODE_SIZE:
                end = start + MAX_CODE_SIZE
            
            code = content[start:end].decode("utf-8", errors="ignore")
            
            # Limit to first 20 lines to avoid too much context
            code_lines = code.split("\n")[:20]
            code = "\n".join(code_lines)
        except Exception:
            return {"name": class_info.get("name", "unknown"), "error": "Could not read class"}
        
        # Check cache
        cache_key = get_cache_key(code)
        cached = load_from_cache(self.cache_dir, cache_key, "docstrings")
        
        if cached:
            return {
                "name": class_info.get("name", "unknown"),
                "docstring": cached["docstring"],
                "cached": True,
            }
        
        # Build context
        context = self._build_context(module_path)
        
        # Generate docstring
        try:
            docstring = self.writer.generate_docstring(code, context)
            
            result = {"docstring": docstring}
            save_to_cache(self.cache_dir, cache_key, result, "docstrings")
            
            return {
                "name": class_info.get("name", "unknown"),
                "docstring": docstring,
                "cached": False,
            }
        except Exception as e:
            return {"name": class_info.get("name", "unknown"), "error": str(e)}
    
    def _build_context(self, module_path: str) -> str:
        """Build context string for a module."""
        context_parts = []
        
        # Add imports
        if module_path in self.ast_data:
            imports = self.ast_data[module_path].get("imports", [])
            if imports:
                # Extract symbol from import dict, handle both dict and string formats
                import_symbols = []
                for imp in imports[:5]:
                    if isinstance(imp, dict):
                        import_symbols.append(imp.get("symbol", str(imp)))
                    else:
                        import_symbols.append(str(imp))
                context_parts.append(f"Imports: {', '.join(import_symbols)}")
        
        # Add dependencies
        internal_deps = self.deps_data.get("internal_dependencies", {}).get(module_path, [])
        if internal_deps:
            context_parts.append(f"Dependencies: {', '.join(internal_deps[:3])}")
        
        return " | ".join(context_parts) if context_parts else "No additional context"
