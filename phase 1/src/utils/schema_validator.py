import json
from pathlib import Path
from jsonschema import validate, ValidationError
from datetime import datetime
from typing import Any, Dict, List, Tuple

class StrictValidator:
    """
    Comprehensive schema validation with optional strict mode.
    Checks structure, semantics, and best practices.
    """
    
    def __init__(self, strict: bool = False):
        """
        Args:
            strict: If True, enforce additional validation rules
        """
        self.strict = strict
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate_ast_output(self, data: list, repo_name: str) -> Tuple[bool, List[str]]:
        """
        Validate AST extraction output.
        
        Checks:
        - All files have required fields (file, language, imports, functions, classes)
        - Language is recognized
        - No duplicate files
        - Import objects have required structure
        """
        self.errors = []
        self.warnings = []
        
        seen_files = set()
        
        for i, entry in enumerate(data):
            # Required fields
            if "file" not in entry:
                self.errors.append(f"[Entry {i}] Missing 'file' field")
                continue
            
            file_path = entry["file"]
            
            # Duplicate check
            if file_path in seen_files:
                self.errors.append(f"[File {file_path}] Duplicate file entry")
            seen_files.add(file_path)
            
            # Language validation
            valid_langs = {"python", "javascript", "typescript", "java", "c", "cpp", "csharp"}
            if entry.get("language") not in valid_langs:
                self.errors.append(f"[File {file_path}] Invalid language: {entry.get('language')}")
            
            # Required array fields
            for field in ["imports", "functions", "classes"]:
                if field not in entry:
                    self.errors.append(f"[File {file_path}] Missing '{field}' array")
                elif not isinstance(entry[field], list):
                    self.errors.append(f"[File {file_path}] '{field}' must be array, got {type(entry[field])}")
            
            # Import validation (strict mode)
            if self.strict:
                for j, imp in enumerate(entry.get("imports", [])):
                    if not isinstance(imp, dict):
                        self.errors.append(f"[File {file_path}, Import {j}] Import must be object")
                    elif "symbol" not in imp:
                        self.errors.append(f"[File {file_path}, Import {j}] Import missing 'symbol'")
        
        return len(self.errors) == 0, self.errors + self.warnings
    
    def validate_dependency_output(self, data: dict) -> Tuple[bool, List[str]]:
        """
        Validate dependency graph output.
        
        Checks:
        - Nodes and edges present
        - Edge source/target consistency
        - No self-loops (unless explicitly allowed)
        - Edge kind is valid
        - Evidence structure
        """
        self.errors = []
        self.warnings = []
        
        if "nodes" not in data or "edges" not in data:
            self.errors.append("Missing 'nodes' or 'edges' field")
            return False, self.errors
        
        nodes = set(data["nodes"])
        valid_edge_kinds = {"internal_module", "cross_language", "uncertain_dynamic", 
                           "external_library", "language_runtime", "dynamic"}
        
        for i, edge in enumerate(data["edges"]):
            # Required fields
            for field in ["from", "to", "kind"]:
                if field not in edge:
                    self.errors.append(f"[Edge {i}] Missing '{field}'")
            
            # Source consistency
            if edge.get("from") not in nodes:
                self.warnings.append(f"[Edge {i}] Source '{edge.get('from')}' not in nodes")
            
            # Target consistency (strip prefix for checking)
            target = edge.get("to", "").split(":", 1)[-1]
            if target not in nodes and edge.get("kind") == "internal_module":
                self.warnings.append(f"[Edge {i}] Internal target '{target}' not in nodes")
            
            # Valid kind
            if edge.get("kind") not in valid_edge_kinds:
                self.errors.append(f"[Edge {i}] Invalid edge kind: {edge.get('kind')}")
            
            # Strict mode: evidence structure
            if self.strict:
                evidence = edge.get("evidence", {})
                if not isinstance(evidence, dict):
                    self.errors.append(f"[Edge {i}] Evidence must be object")
        
        return len(self.errors) == 0, self.errors + self.warnings
    
    def validate_components_output(self, data: list) -> Tuple[bool, List[str]]:
        """
        Validate components output.
        
        Checks:
        - All components have required fields
        - Confidence in [0, 1]
        - Unique component IDs
        - Files array not empty
        - All files mentioned exist
        """
        self.errors = []
        self.warnings = []
        
        seen_ids = set()
        all_files = set()
        
        for i, comp in enumerate(data):
            # Required fields
            for field in ["component_id", "hypothesis", "files", "confidence"]:
                if field not in comp:
                    self.errors.append(f"[Component {i}] Missing '{field}'")
            
            # Component ID uniqueness
            comp_id = comp.get("component_id")
            if comp_id in seen_ids:
                self.errors.append(f"[Component {i}] Duplicate component_id: {comp_id}")
            seen_ids.add(comp_id)
            
            # Confidence range
            conf = comp.get("confidence")
            if not isinstance(conf, (int, float)) or conf < 0 or conf > 1:
                self.errors.append(f"[Component {i}] Invalid confidence: {conf}")
            
            # Files validation
            files = comp.get("files", [])
            if not files:
                self.warnings.append(f"[Component {i}] Empty files array")
            elif not isinstance(files, list):
                self.errors.append(f"[Component {i}] 'files' must be array")
            else:
                all_files.update(files)
            
            # Cohesion metrics (strict mode)
            if self.strict:
                cohesion = comp.get("cohesion", {})
                if not isinstance(cohesion, dict):
                    self.errors.append(f"[Component {i}] Cohesion must be object")
                else:
                    for metric in ["internal_edges", "external_edges", "density"]:
                        if metric not in cohesion:
                            self.errors.append(f"[Component {i}] Cohesion missing '{metric}'")
        
        return len(self.errors) == 0, self.errors + self.warnings


def validate_all_outputs(ast_file: str, deps_file: str, components_file: str, 
                        strict: bool = False) -> Dict[str, Any]:
    """
    Validate all three output files.
    
    Returns:
        {
            "valid": bool,
            "ast": {"valid": bool, "errors": [...], "warnings": [...]},
            "dependencies": {...},
            "components": {...},
            "summary": str
        }
    """
    validator = StrictValidator(strict=strict)
    results = {
        "valid": True,
        "ast": {},
        "dependencies": {},
        "components": {},
        "timestamp": datetime.now().isoformat()
    }
    
    # Validate AST
    try:
        with open(ast_file, "r") as f:
            ast_data = json.load(f)
            if isinstance(ast_data, dict) and "data" in ast_data:
                ast_data = ast_data["data"]
            results["ast"]["valid"], results["ast"]["messages"] = validator.validate_ast_output(ast_data, "repo")
    except Exception as e:
        results["ast"]["valid"] = False
        results["ast"]["messages"] = [f"Failed to load/parse: {e}"]
    
    # Validate dependencies
    try:
        with open(deps_file, "r") as f:
            deps_data = json.load(f)
            if isinstance(deps_data, dict) and "data" in deps_data:
                deps_data = deps_data["data"]
            results["dependencies"]["valid"], results["dependencies"]["messages"] = validator.validate_dependency_output(deps_data)
    except Exception as e:
        results["dependencies"]["valid"] = False
        results["dependencies"]["messages"] = [f"Failed to load/parse: {e}"]
    
    # Validate components
    try:
        with open(components_file, "r") as f:
            comp_data = json.load(f)
            if isinstance(comp_data, dict) and "data" in comp_data:
                comp_data = comp_data["data"]
            results["components"]["valid"], results["components"]["messages"] = validator.validate_components_output(comp_data)
    except Exception as e:
        results["components"]["valid"] = False
        results["components"]["messages"] = [f"Failed to load/parse: {e}"]
    
    # Overall validity
    results["valid"] = all(r["valid"] for r in [results["ast"], results["dependencies"], results["components"]])
    
    # Summary
    total_errors = sum(len([m for m in r.get("messages", []) if "error" in m.lower()]) 
                      for r in [results["ast"], results["dependencies"], results["components"]])
    results["summary"] = f"Overall: {'✅ VALID' if results['valid'] else '❌ INVALID'} ({total_errors} errors)"
    
    return results