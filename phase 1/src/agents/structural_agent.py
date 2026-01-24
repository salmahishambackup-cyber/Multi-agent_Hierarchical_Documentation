import os
from utils.schema_validator import validate_all_outputs
from agents.base_agent import BaseAgent
from analysis.file_metrics import FileMetricsExtractor, aggregate_repository_metrics
from utils.determinism import DeterminismEnforcer, DeterminismReport
from utils.edge_case_handler import CircularImportDetector, MonolithicFileDetector, GeneratedCodeDetector, EdgeCaseReport
from utils.performance_metrics import PerformanceMonitor, OptimizationLogger

from utils.repo_scanner import clone_repo, scan_repo_files
from utils.file_filter import is_allowed_file
from utils.file_loader import load_file_bytes
from utils.json_writer import write_json

from analysis.ast_extractor import extract_ast_info
from analysis.dependency_builder import build_dependency_graph
from analysis.dependency_builder import extract_cross_language_calls
from analysis.component_extractor import extract_components


class StructuralAgent(BaseAgent):
    """
    StructuralAgent is responsible for Phase (1):
    - AST-based static analysis
    - Dependency graph construction
    - High-level code component extraction
    """

    def __init__(self):
        super().__init__("StructuralAgent")
        self.perf_monitor = PerformanceMonitor()
        self.opt_logger = OptimizationLogger()

    def run(self, repo_url: str):
        # =========================
        # 0. Initialize Performance Monitoring
        # =========================
        self.perf_monitor.start_monitoring()
        
        # =========================
        # 1. Clone repository
        # =========================
        self.perf_monitor.start_stage("Clone Repository")
        if repo_url.startswith("http://") or repo_url.startswith("https://") or repo_url.startswith("git@"):
            repo_path = clone_repo(repo_url, "data/repos")
        else:
            repo_path = repo_url  # Assume it's a local path
        repo_name = os.path.basename(repo_path.rstrip("/"))
        self.perf_monitor.end_stage("Clone Repository")

        # =========================
        # 2. Scan repository files
        # =========================
        self.perf_monitor.start_stage("Scan Repository")
        files = scan_repo_files(repo_path)
        self.perf_monitor.end_stage("Scan Repository", items_processed=len(files), files_scanned=len(files))

        # =========================
        # 3. Filter files
        # =========================
        self.perf_monitor.start_stage("Filter Files")
        files = [f for f in files if is_allowed_file(f)]
        self.perf_monitor.end_stage("Filter Files", items_processed=len(files), files_allowed=len(files))
        

        # =========================
        # 4. AST Extraction (STEP 1)
        # =========================
        self.perf_monitor.start_stage("AST Extraction")
        ast_summaries = []

        for file_path in files:
            try:
                f_path = os.path.abspath(os.path.join(repo_path, file_path))
                content = load_file_bytes(f_path)
            except Exception:
                continue

            ast_info = extract_ast_info(f_path, content, repo_root=repo_path)
            if ast_info:
                ast_summaries.append(ast_info)
        
        self.perf_monitor.end_stage("AST Extraction", items_processed=len(ast_summaries), 
                                     files_analyzed=len(ast_summaries), total_files=len(files))

        # =========================
        # 4.5 Extract File Metrics
        # =========================
        self.perf_monitor.start_stage("File Metrics Extraction")
        metrics_extractor = FileMetricsExtractor()
        for summary in ast_summaries:
            try:
                f_path = os.path.abspath(os.path.join(repo_path, summary["file"]))
                content = load_file_bytes(f_path)
                metrics = metrics_extractor.extract_metrics(summary, content, summary.get("language", "unknown"))
                summary["metrics"] = metrics
            except Exception as e:
                summary["metrics"] = {"error": str(e)}

        # Aggregate metrics
        repo_metrics = aggregate_repository_metrics(ast_summaries)

        # Store for later reference
        self._ast_summaries = ast_summaries
        self._repo_metrics = repo_metrics
        self.perf_monitor.end_stage("File Metrics Extraction", items_processed=len(ast_summaries),
                                     metrics_extracted=len(ast_summaries))

        # =========================
        # 5. Dependency Graph
        # =========================
        self.perf_monitor.start_stage("Dependency Graph Construction")
        dependency_graph = build_dependency_graph(ast_summaries, repo_path)

        self._dependency_graph = dependency_graph
        self.perf_monitor.end_stage("Dependency Graph Construction", 
                                     items_processed=len(dependency_graph.get('nodes', [])),
                                     nodes=len(dependency_graph.get('nodes', [])),
                                     edges=len(dependency_graph.get('edges', [])))

        # =========================
        # 5.5 Cross-Language Analysis
        # =========================
        self.perf_monitor.start_stage("Cross-Language Analysis")
        cross_language_calls = extract_cross_language_calls(
            ast_summaries, 
            dependency_graph
        )
        self.perf_monitor.end_stage("Cross-Language Analysis", 
                                     items_processed=len(cross_language_calls) if cross_language_calls else 0)
        
        if cross_language_calls:
            write_json(
                f"data/artifacts/{repo_name}/dependencies_cross_language.json",
                cross_language_calls,
                metadata={
                    "agent": self.name,
                    "stage": "cross_language_analysis"
                }
            )

        # =========================
        # 5.5 Edge Case Analysis (STEP 2.5)
        # =========================
        self.perf_monitor.start_stage("Edge Case Analysis")
        # Detect circular imports
        cycles = CircularImportDetector.find_cycles(dependency_graph)
        
        # Detect monolithic files
        monolithic_files = MonolithicFileDetector.identify_monolithic_files(self._ast_summaries)
        
        # Detect generated code
        generated_files = GeneratedCodeDetector.detect_in_batch(self._ast_summaries)
        
        # Store for later reporting
        self._edge_cases = {
            "cycles": cycles,
            "monolithic_files": monolithic_files,
            "generated_files": generated_files
        }
        self.perf_monitor.end_stage("Edge Case Analysis", 
                                     items_processed=len(cycles) + len(monolithic_files) + len(generated_files),
                                     cycles=len(cycles), monolithic=len(monolithic_files), 
                                     generated=len(generated_files))


        # =========================
        # 6. High-level Components (STEP 3)
        # =========================
        self.perf_monitor.start_stage("Component Extraction")
        components = extract_components(ast_summaries, dependency_graph)
        self.perf_monitor.end_stage("Component Extraction", 
                                     items_processed=len(components),
                                     components=len(components))

        # =========================
        # 6.5 Edge Case Reporting
        # =========================
        self.perf_monitor.start_stage("Edge Case Reporting")
        edge_case_report = EdgeCaseReport()
        edge_case_report.add_circular_imports(self._edge_cases["cycles"], dependency_graph)
        edge_case_report.add_monolithic_files(self._edge_cases["monolithic_files"])
        edge_case_report.add_generated_files(self._edge_cases["generated_files"])
        edge_case_report.compute_summary()
        edge_case_report.print_summary()
        self.perf_monitor.end_stage("Edge Case Reporting")

        # =========================
        # 7. Apply Determinism
        # =========================
        self.perf_monitor.start_stage("Determinism Enforcement")
        print(f"\n[APPLYING DETERMINISM]")
        
        # Make all data deterministic (sort dicts, normalize floats, convert sets)
        ast_summaries_det = DeterminismEnforcer.make_deterministic(self._ast_summaries)
        dependency_graph_det = DeterminismEnforcer.make_deterministic(self._dependency_graph)
        components_det = DeterminismEnforcer.make_deterministic(components)
        
        # Create determinism report with version checks
        det_report = DeterminismReport()
        det_report.add_artifact_hash("ast", ast_summaries_det)
        det_report.add_artifact_hash("dependencies", dependency_graph_det)
        det_report.add_artifact_hash("components", components_det)
        
        # Print determinism report to console
        det_report.print_summary()
        
        # Combine with edge case analysis for complete metadata
        combined_metadata = {
            **det_report.to_dict(),
            **edge_case_report.to_dict()
        }
        
        # =========================
        # 8. Write All Deterministic Outputs
        # =========================
        # Write AST with determinism + edge case metadata
        write_json(
            f"data/artifacts/{repo_name}/ast.json",
            ast_summaries_det,
            metadata={
                "agent": self.name,
                "stage": "ast_extraction",
                "repository_metrics": self._repo_metrics,
                **combined_metadata
            }
        )
        
        # Write dependency graph with determinism + edge case metadata
        write_json(
            f"data/artifacts/{repo_name}/dependencies.json",
            dependency_graph_det,
            metadata={
                "agent": self.name,
                "stage": "dependency_graph",
                **combined_metadata
            }
        )
        
        write_json(
            f"data/artifacts/{repo_name}/dependencies_normalized.json",
            dependency_graph_det,
            metadata={
                "agent": self.name,
                "stage": "dependency_graph_normalized",
                **combined_metadata
            }
        )
        
        # Write components with determinism metadata
        write_json(
            f"data/artifacts/{repo_name}/components.json",
            components_det,
            metadata={
                "agent": self.name,
                "stage": "components",
                **combined_metadata
            }
        )
        
        self.perf_monitor.end_stage("Determinism Enforcement",
                                     items_processed=3,  # 3 artifacts determinized
                                     artifacts_determinized=3)

        # =========================
        # 9. Validation & Summary (on deterministic versions)
        # =========================
        self.perf_monitor.start_stage("Output Validation")
        validation_results = validate_all_outputs(
            f"data/artifacts/ast/{repo_name}.json",
            f"data/artifacts/dependencies/{repo_name}.json",
            f"data/artifacts/components/{repo_name}.json",
            strict=True  # Enable strict mode for production
        )
        self.perf_monitor.end_stage("Output Validation",
                                     items_processed=3,  # 3 artifact types validated
                                     artifacts_validated=3)

        print(f"\n[OUTPUT VALIDATION]")
        print(validation_results["summary"])
        if validation_results["ast"]["messages"]:
            print(f"AST: {validation_results['ast']['messages'][:3]}")
        if validation_results["dependencies"]["messages"]:
            print(f"Dependencies: {validation_results['dependencies']['messages'][:3]}")
        if validation_results["components"]["messages"]:
            print(f"Components: {validation_results['components']['messages'][:3]}")

        # Print metrics summary (deferred from Step 4)
        print(f"\n[REPOSITORY METRICS]")
        print(f"Total files: {self._repo_metrics['total_files']}")
        print(f"Total LOC: {self._repo_metrics['total_loc']}")
        print(f"Avg LOC/file: {self._repo_metrics['avg_loc_per_file']}")
        print(f"Languages: {self._repo_metrics['language_distribution']}")
        print(f"Size distribution: {self._repo_metrics['size_distribution']}")
        print(f"Complexity: {self._repo_metrics['complexity_distribution']}")

        # =========================
        # 10. Performance Monitoring & Reporting
        # =========================
        self.perf_monitor.end_monitoring()
        self.perf_monitor.print_summary()
        
        # Print optimization insights
        self.opt_logger.print_summary()

        return {
            "repo": repo_name,
            "artifacts": {
                "ast": f"data/artifacts/ast/{repo_name}.json",
                "dependencies": f"data/artifacts/dependencies/{repo_name}.json",
                "components": f"data/artifacts/components/{repo_name}.json"
            }
        }

