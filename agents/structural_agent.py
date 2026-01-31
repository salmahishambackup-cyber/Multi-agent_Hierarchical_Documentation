"""Structural Agent for Phase 1 static code analysis."""

from typing import Dict, Any, List
from pathlib import Path
from tqdm import tqdm

# Don't import BaseAgent to avoid torch import issues
# from agents.base_agent import BaseAgent
from analyzer import (
    extract_ast_info,
    build_dependency_graph,
    extract_components,
    detect_language,
)
from utils.repo_scanner import scan_repo_files, clone_repo
from utils.file_filter import is_allowed_file, filter_source_files
from utils.file_loader import load_file_bytes
from utils.json_writer import write_json_with_timestamp
from utils.determinism import DeterminismEnforcer
from utils.edge_case_handler import analyze_edge_cases
from utils.performance_metrics import PerformanceMonitor, OptimizationLogger
from utils.schema_validator import validate_all_outputs
from utils.path_utils import normalize_path


class StructuralAgent:
    """
    Phase 1: Static code analysis agent.
    
    Orchestrates:
    - Repository cloning/scanning
    - File filtering
    - AST extraction
    - File metrics extraction
    - Dependency graph building
    - Cross-language analysis
    - Edge case analysis
    - Component extraction
    - Determinism enforcement
    - Output validation
    - Performance monitoring
    """
    
    def __init__(
        self,
        repo_path: str,
        artifacts_dir: str = "./artifacts",
        enable_performance_monitoring: bool = True,
        enable_edge_case_detection: bool = True,
        enable_validation: bool = True,
    ):
        """
        Initialize structural agent.
        
        Args:
            repo_path: Path to repository (local path or URL)
            artifacts_dir: Directory for artifacts
            enable_performance_monitoring: Enable performance tracking
            enable_edge_case_detection: Enable edge case detection
            enable_validation: Enable output validation
        """
        self.repo_path = Path(repo_path).resolve()
        self.artifacts_dir = Path(artifacts_dir).resolve()
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        
        self.enable_performance_monitoring = enable_performance_monitoring
        self.enable_edge_case_detection = enable_edge_case_detection
        self.enable_validation = enable_validation
        
        self.monitor = PerformanceMonitor() if enable_performance_monitoring else None
        self.optimizer = OptimizationLogger() if enable_performance_monitoring else None
        
        # Check if repo_path is a URL
        if str(repo_path).startswith(("http://", "https://", "git@")):
            print(f"Cloning repository: {repo_path}")
            self.repo_path = Path(clone_repo(str(repo_path)))
            print(f"Repository cloned to: {self.repo_path}")
    
    def run(self) -> Dict[str, Any]:
        """
        Run Phase 1 static analysis.
        
        Returns:
            Dictionary with analysis results and artifact paths
        """
        print("\n━━━ PHASE 1: Structural Analysis ━━━")
        
        # Start overall monitoring
        if self.monitor:
            self.monitor.start_stage("Overall Analysis")
        
        # 1. Scan repository files
        if self.monitor:
            self.monitor.start_stage("File Scanning")
        
        source_files = self._scan_repository()
        print(f"Found {len(source_files)} source files")
        
        if self.monitor:
            self.monitor.end_stage()
        
        # 2. Extract AST information
        if self.monitor:
            self.monitor.start_stage("AST Extraction")
        
        ast_data, file_contents = self._extract_ast(source_files)
        print(f"Parsed {len(ast_data)} files")
        
        if self.monitor:
            stage = self.monitor.end_stage()
            if self.optimizer and stage:
                self.optimizer.suggest_if_slow("AST Extraction", stage.duration, threshold=30.0)
        
        # 3. Build dependency graph
        if self.monitor:
            self.monitor.start_stage("Dependency Analysis")
        
        deps_data = self._build_dependencies(ast_data)
        print(f"Found {len(deps_data.get('edges', []))} dependencies")
        
        if self.monitor:
            self.monitor.end_stage()
        
        # 4. Extract components
        if self.monitor:
            self.monitor.start_stage("Component Extraction")
        
        components_data = self._extract_components(ast_data, deps_data)
        print(f"Identified {len(components_data)} components")
        
        if self.monitor:
            self.monitor.end_stage()
        
        # 5. Edge case analysis
        edge_case_report = None
        if self.enable_edge_case_detection:
            if self.monitor:
                self.monitor.start_stage("Edge Case Detection")
            
            edge_case_report = self._analyze_edge_cases(ast_data, deps_data, file_contents)
            
            if self.monitor:
                self.monitor.end_stage()
        
        # 6. Enforce determinism
        if self.monitor:
            self.monitor.start_stage("Determinism Enforcement")
        
        ast_data = DeterminismEnforcer.enforce_determinism(ast_data)
        deps_data = DeterminismEnforcer.enforce_determinism(deps_data)
        components_data = DeterminismEnforcer.enforce_determinism(components_data)
        
        if self.monitor:
            self.monitor.end_stage()
        
        # 7. Save artifacts
        if self.monitor:
            self.monitor.start_stage("Artifact Saving")
        
        artifact_paths = self._save_artifacts(
            ast_data, deps_data, components_data, edge_case_report
        )
        
        if self.monitor:
            self.monitor.end_stage()
        
        # 8. Validate outputs
        if self.enable_validation:
            if self.monitor:
                self.monitor.start_stage("Output Validation")
            
            validation_reports = self._validate_outputs(
                artifact_paths["ast_path"],
                artifact_paths["deps_path"],
                artifact_paths["components_path"]
            )
            
            # Print validation results
            for output_type, report in validation_reports.items():
                if not report.is_valid:
                    print(f"⚠️  Validation warnings for {output_type}:")
                    for error in report.errors:
                        print(f"  - {error.field}: {error.error}")
            
            if self.monitor:
                self.monitor.end_stage()
        
        # End overall monitoring
        if self.monitor:
            self.monitor.end_stage()
            self.monitor.print_summary()
        
        if self.optimizer:
            self.optimizer.print_suggestions()
        
        # Compute summary stats
        total_functions = sum(
            len(info.get("functions", [])) for info in ast_data.values()
        )
        total_classes = sum(
            len(info.get("classes", [])) for info in ast_data.values()
        )
        
        print(f"✅ {len(ast_data)} modules, {total_functions} functions, {total_classes} classes")
        
        return {
            **artifact_paths,
            "stats": {
                "modules": len(ast_data),
                "functions": total_functions,
                "classes": total_classes,
            },
            "ast_data": ast_data,
            "deps_data": deps_data,
            "components_data": components_data,
            "edge_case_report": edge_case_report.to_dict() if edge_case_report else None,
            "performance_summary": self.monitor.get_summary() if self.monitor else None,
        }
    
    def _scan_repository(self) -> List[Path]:
        """Scan repository for source files."""
        # Get all files with supported extensions
        all_files = scan_repo_files(str(self.repo_path))
        
        # Filter to only source files
        source_files = filter_source_files(all_files)
        
        return source_files
    
    def _extract_ast(self, source_files: List[Path]) -> tuple[Dict[str, Any], Dict[str, bytes]]:
        """
        Extract AST information from source files.
        
        Returns:
            Tuple of (ast_data, file_contents)
        """
        ast_data = {}
        file_contents = {}
        
        for file_path in tqdm(source_files, desc="Extracting AST"):
            rel_path = normalize_path(file_path, self.repo_path)
            
            try:
                content = load_file_bytes(str(file_path))
                if content is None:
                    continue
                
                file_contents[rel_path] = content
                
                ast_info = extract_ast_info(
                    str(file_path), 
                    content, 
                    str(self.repo_path)
                )
                
                if ast_info:
                    ast_data[rel_path] = ast_info
            except Exception as e:
                print(f"Warning: Failed to parse {rel_path}: {e}")
        
        return ast_data, file_contents
    
    def _build_dependencies(self, ast_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build dependency graph."""
        ast_list = list(ast_data.values())
        return build_dependency_graph(ast_list, str(self.repo_path))
    
    def _extract_components(
        self, 
        ast_data: Dict[str, Any], 
        deps_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract components."""
        ast_list = list(ast_data.values())
        return extract_components(ast_list, deps_data)
    
    def _analyze_edge_cases(
        self,
        ast_data: Dict[str, Any],
        deps_data: Dict[str, Any],
        file_contents: Dict[str, bytes]
    ) -> Any:
        """Analyze edge cases."""
        report = analyze_edge_cases(ast_data, deps_data, file_contents=file_contents)
        
        if report.has_issues():
            print(f"\n⚠️  Edge Cases Detected:")
            if report.circular_imports:
                print(f"  - {len(report.circular_imports)} circular import(s)")
            if report.monolithic_files:
                print(f"  - {len(report.monolithic_files)} monolithic file(s)")
            if report.generated_files:
                print(f"  - {len(report.generated_files)} generated file(s)")
        
        return report
    
    def get_artifact_path(self, filename: str) -> Path:
        """
        Get path for an artifact file.
        
        Args:
            filename: Name of the artifact file
            
        Returns:
            Full path to artifact
        """
        return self.artifacts_dir / filename
    
    def _save_artifacts(
        self,
        ast_data: Dict[str, Any],
        deps_data: Dict[str, Any],
        components_data: List[Dict[str, Any]],
        edge_case_report: Any = None
    ) -> Dict[str, str]:
        """Save all artifacts to disk."""
        ast_path = self.get_artifact_path("ast.json")
        deps_path = self.get_artifact_path("dependencies_normalized.json")
        components_path = self.get_artifact_path("components.json")
        
        # Save main artifacts
        write_json_with_timestamp(ast_path, ast_data)
        write_json_with_timestamp(
            deps_path,
            {
                "internal_dependencies": self._extract_internal_deps(deps_data),
                "external_dependencies": self._extract_external_deps(deps_data),
                "raw_graph": deps_data,
            }
        )
        write_json_with_timestamp(components_path, components_data)
        
        # Save edge case report if available
        if edge_case_report:
            edge_case_path = self.get_artifact_path("edge_cases.json")
            write_json_with_timestamp(edge_case_path, edge_case_report.to_dict())
        
        return {
            "ast_path": str(ast_path),
            "deps_path": str(deps_path),
            "components_path": str(components_path),
        }
    
    def _extract_internal_deps(self, deps_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Extract internal dependencies from graph."""
        from collections import defaultdict
        
        internal_deps = defaultdict(list)
        for edge in deps_data.get("edges", []):
            if edge.get("kind") in ["internal_module", "cross_language"]:
                from_file = edge.get("from")
                to_file = edge.get("to")
                if from_file and to_file:
                    internal_deps[from_file].append(to_file)
        
        return dict(internal_deps)
    
    def _extract_external_deps(self, deps_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Extract external dependencies from graph."""
        from collections import defaultdict
        
        external_deps = defaultdict(list)
        for edge in deps_data.get("edges", []):
            if edge.get("kind") in ["external_library", "language_runtime"]:
                from_file = edge.get("from")
                to_file = edge.get("to")
                if from_file and to_file:
                    # Remove prefixes
                    to_file = to_file.replace("external:", "")
                    external_deps[from_file].append(to_file)
        
        return dict(external_deps)
    
    def _validate_outputs(
        self,
        ast_path: str,
        deps_path: str,
        components_path: str
    ) -> Dict[str, Any]:
        """Validate output artifacts."""
        return validate_all_outputs(
            ast_path=Path(ast_path),
            deps_path=Path(deps_path),
            components_path=Path(components_path)
        )
