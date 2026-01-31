"""Schema validation utilities."""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class ValidationError:
    """Validation error information."""
    path: str
    field: str
    error: str


@dataclass
class ValidationReport:
    """Validation report."""
    is_valid: bool = True
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def add_error(self, path: str, field: str, error: str) -> None:
        """Add a validation error."""
        self.is_valid = False
        self.errors.append(ValidationError(path=path, field=field, error=error))
    
    def add_warning(self, message: str) -> None:
        """Add a validation warning."""
        self.warnings.append(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_valid": self.is_valid,
            "errors": [
                {"path": e.path, "field": e.field, "error": e.error}
                for e in self.errors
            ],
            "warnings": self.warnings
        }


def validate_ast_output(ast_data: Dict[str, Any]) -> ValidationReport:
    """
    Validate AST output format.
    
    Args:
        ast_data: AST data to validate
        
    Returns:
        ValidationReport
    """
    report = ValidationReport()
    
    if not isinstance(ast_data, dict):
        report.add_error("ast_data", "root", "Must be a dictionary")
        return report
    
    for file_path, file_data in ast_data.items():
        if not isinstance(file_data, dict):
            report.add_error(file_path, "file_data", "Must be a dictionary")
            continue
        
        # Check required fields
        required_fields = ["file", "language"]
        for field in required_fields:
            if field not in file_data:
                report.add_error(file_path, field, f"Missing required field: {field}")
        
        # Check optional fields have correct types
        if "imports" in file_data and not isinstance(file_data["imports"], list):
            report.add_error(file_path, "imports", "Must be a list")
        
        if "functions" in file_data and not isinstance(file_data["functions"], list):
            report.add_error(file_path, "functions", "Must be a list")
        
        if "classes" in file_data and not isinstance(file_data["classes"], list):
            report.add_error(file_path, "classes", "Must be a list")
    
    return report


def validate_dependency_output(deps_data: Dict[str, Any]) -> ValidationReport:
    """
    Validate dependency graph output format.
    
    Args:
        deps_data: Dependency data to validate
        
    Returns:
        ValidationReport
    """
    report = ValidationReport()
    
    if not isinstance(deps_data, dict):
        report.add_error("deps_data", "root", "Must be a dictionary")
        return report
    
    # Check for nodes and edges
    if "nodes" not in deps_data:
        report.add_error("deps_data", "nodes", "Missing 'nodes' field")
    elif not isinstance(deps_data["nodes"], list):
        report.add_error("deps_data", "nodes", "Must be a list")
    
    if "edges" not in deps_data:
        report.add_error("deps_data", "edges", "Missing 'edges' field")
    elif not isinstance(deps_data["edges"], list):
        report.add_error("deps_data", "edges", "Must be a list")
    else:
        # Validate edges structure
        for i, edge in enumerate(deps_data["edges"]):
            if not isinstance(edge, dict):
                report.add_error("deps_data", f"edges[{i}]", "Must be a dictionary")
                continue
            
            required_edge_fields = ["from", "to"]
            for field in required_edge_fields:
                if field not in edge:
                    report.add_error("deps_data", f"edges[{i}].{field}", "Missing required field")
    
    return report


def validate_component_output(components_data: List[Any]) -> ValidationReport:
    """
    Validate component output format.
    
    Args:
        components_data: Component data to validate
        
    Returns:
        ValidationReport
    """
    report = ValidationReport()
    
    if not isinstance(components_data, list):
        report.add_error("components_data", "root", "Must be a list")
        return report
    
    for i, component in enumerate(components_data):
        if not isinstance(component, dict):
            report.add_error("components_data", f"component[{i}]", "Must be a dictionary")
            continue
        
        # Check for files field
        if "files" not in component:
            report.add_error("components_data", f"component[{i}].files", "Missing 'files' field")
        elif not isinstance(component["files"], list):
            report.add_error("components_data", f"component[{i}].files", "Must be a list")
    
    return report


def validate_all_outputs(
    ast_path: Optional[Path] = None,
    deps_path: Optional[Path] = None,
    components_path: Optional[Path] = None,
    ast_data: Optional[Dict[str, Any]] = None,
    deps_data: Optional[Dict[str, Any]] = None,
    components_data: Optional[List[Any]] = None
) -> Dict[str, ValidationReport]:
    """
    Validate all Phase 1 outputs.
    
    Args:
        ast_path: Path to AST JSON file
        deps_path: Path to dependencies JSON file
        components_path: Path to components JSON file
        ast_data: AST data (if not loading from file)
        deps_data: Dependency data (if not loading from file)
        components_data: Component data (if not loading from file)
        
    Returns:
        Dictionary of validation reports
    """
    reports = {}
    
    # Validate AST
    if ast_data is None and ast_path:
        with open(ast_path) as f:
            ast_data = json.load(f)
    
    if ast_data is not None:
        reports["ast"] = validate_ast_output(ast_data)
    
    # Validate dependencies
    if deps_data is None and deps_path:
        with open(deps_path) as f:
            deps_data = json.load(f)
    
    if deps_data is not None:
        # Handle wrapped format
        if "data" in deps_data:
            deps_data = deps_data["data"]
        if "raw_graph" in deps_data:
            deps_data = deps_data["raw_graph"]
        
        reports["dependencies"] = validate_dependency_output(deps_data)
    
    # Validate components
    if components_data is None and components_path:
        with open(components_path) as f:
            components_data = json.load(f)
    
    if components_data is not None:
        reports["components"] = validate_component_output(components_data)
    
    return reports
