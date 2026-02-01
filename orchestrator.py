"""
Orchestrator for coordinating all pipeline phases.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, Optional

from phase1_analysis import Analyzer, StructuralAgent
from phase2_docstrings import DocstringGenerator, Writer
from phase3_readme import ReadmeGenerator
from phase4_validation import Validator, Critic
from phase5_evaluation import Evaluator
from utils.llm_client import LLMClient
from utils import ensure_dir


class Orchestrator:
    """
    Coordinates all 5 phases of the documentation pipeline.
    """
    
    def __init__(
        self,
        repo_path: str,
        artifacts_dir: str = "./artifacts",
        model_id: str = "Qwen/Qwen2.5-Coder-1.5B-Instruct",
        device: str = "auto",
        quantize: bool = True,
        use_structural_agent: bool = True,
    ):
        """
        Initialize orchestrator.
        
        Args:
            repo_path: Path to repository to document
            artifacts_dir: Directory for artifacts
            model_id: HuggingFace model ID
            device: Device (auto/cpu/cuda)
            quantize: Use 4-bit quantization
            use_structural_agent: Use enhanced StructuralAgent for Phase 1 (default: True)
        """
        self.repo_path = Path(repo_path).resolve()
        self.project_name = self.repo_path.name
        self.artifacts_dir = Path(artifacts_dir).resolve()
        self.cache_dir = self.artifacts_dir / "cache"
        self.use_structural_agent = use_structural_agent
        
        ensure_dir(self.artifacts_dir)
        ensure_dir(self.cache_dir)
        
        # Initialize LLM client (lazy - only when needed)
        self.model_id = model_id
        self.device = device
        self.quantize = quantize
        self.llm_client: Optional[LLMClient] = None
        self.writer: Optional[Writer] = None
        self.critic: Optional[Critic] = None
        
        # Results storage
        self.results = {}
    
    def _ensure_llm(self):
        """Lazily initialize LLM client and agents."""
        if self.llm_client is None:
            self.llm_client = LLMClient(
                model_id=self.model_id,
                device=self.device,
                quantize=self.quantize,
            )
            self.writer = Writer(self.llm_client)
            self.critic = Critic()
    
    def run_phase1(self) -> Dict[str, Any]:
        """
        Run Phase 1: Static analysis.
        
        Outputs:
            - <artifacts_dir>/ast.json - AST data for all modules
            - <artifacts_dir>/dependencies_normalized.json - Dependency graph
            - <artifacts_dir>/components.json - Component clusters
            - <artifacts_dir>/edge_cases.json - Edge case analysis (if enabled)
        """
        print("\n━━━ PHASE 1: Analysis ━━━")
        
        if self.use_structural_agent:
            # Use enhanced StructuralAgent
            analyzer = StructuralAgent(
                repo_path=str(self.repo_path),
                artifacts_dir=str(self.artifacts_dir),
                enable_performance_monitoring=True,
                enable_edge_case_detection=True,
                enable_validation=True,
            )
        else:
            # Use legacy Analyzer
            analyzer = Analyzer(
                repo_path=str(self.repo_path),
                artifacts_dir=str(self.artifacts_dir),
            )
        
        results = analyzer.run()
        self.results["phase1"] = results
        
        # Print output locations
        if "artifacts" in results:
            print(f"\n📁 Phase 1 outputs saved to:")
            for key, path in results["artifacts"].items():
                print(f"   • {key}: {path}")
        
        return results
    
    def run_phase2(self) -> Dict[str, Any]:
        """
        Run Phase 2: Docstring generation.
        
        Outputs:
            - <artifacts_dir>/doc_artifacts.json - Generated docstrings
            - <artifacts_dir>/cache/ - LLM response cache
        """
        print("\n━━━ PHASE 2: Docstrings ━━━")
        
        if "phase1" not in self.results:
            raise ValueError("Phase 1 must be run before Phase 2")
        
        self._ensure_llm()
        
        generator = DocstringGenerator(
            writer=self.writer,
            repo_path=str(self.repo_path),
            artifacts_dir=str(self.artifacts_dir),
            cache_dir=str(self.cache_dir),
            ast_data=self.results["phase1"]["ast_data"],
            deps_data=self.results["phase1"]["deps_data"],
        )
        
        results = generator.run()
        self.results["phase2"] = results
        
        # Print output location
        if "output_path" in results:
            print(f"📁 Phase 2 output saved to: {results['output_path']}")
        
        return results
    
    def run_phase3(self) -> Dict[str, Any]:
        """
        Run Phase 3: README generation.
        
        Outputs:
            - <repo_path>/README.md - Generated README file (saved to repository root)
        """
        print("\n━━━ PHASE 3: README ━━━")
        
        if "phase1" not in self.results:
            raise ValueError("Phase 1 must be run before Phase 3")
        
        self._ensure_llm()
        
        generator = ReadmeGenerator(
            writer=self.writer,
            repo_path=str(self.repo_path),
            artifacts_dir=str(self.artifacts_dir),
            project_name=self.project_name,
            analysis_results=self.results["phase1"],
        )
        
        results = generator.run()
        self.results["phase3"] = results
        
        # Output location already printed by ReadmeGenerator
        return results
    
    def run_phase4(self) -> Dict[str, Any]:
        """
        Run Phase 4: Validation.
        
        Outputs:
            - No file output (validation results returned in memory only)
        """
        print("\n━━━ PHASE 4: Validation ━━━")
        
        if "phase3" not in self.results:
            raise ValueError("Phase 3 must be run before Phase 4")
        
        self._ensure_llm()
        
        validator = Validator(
            writer=self.writer,
            critic=self.critic,
            repo_path=str(self.repo_path),
            readme_content=self.results["phase3"]["content"],
        )
        
        results = validator.run()
        self.results["phase4"] = results
        
        print("📋 Phase 4 validation results (in-memory, no file saved)")
        
        return results
    
    def run_phase5(self) -> Dict[str, Any]:
        """
        Run Phase 5: Evaluation.
        
        Outputs:
            - <artifacts_dir>/evaluation_report.json - Quality scores and feedback
        """
        print("\n━━━ PHASE 5: Evaluation ━━━")
        
        if "phase3" not in self.results:
            raise ValueError("Phase 3 must be run before Phase 5")
        
        self._ensure_llm()
        
        # Use updated content from phase 4 if available
        readme_content = self.results["phase3"]["content"]
        if "phase4" in self.results and "updated_content" in self.results["phase4"]:
            readme_content = self.results["phase4"]["updated_content"]
        
        evaluator = Evaluator(
            writer=self.writer,
            artifacts_dir=str(self.artifacts_dir),
            readme_content=readme_content,
        )
        
        results = evaluator.run()
        self.results["phase5"] = results
        
        # Print output location (already printed by Evaluator, but add reminder)
        if "report_path" in results:
            print(f"📁 Phase 5 output saved to: {results['report_path']}")
        
        return results
    
    def run_all(self) -> Dict[str, Any]:
        """Run all 5 phases in sequence."""
        print(f"\n🤖 Documentation Assistant")
        print(f"Project: {self.project_name}")
        print(f"Path: {self.repo_path}")
        print(f"Artifacts Directory: {self.artifacts_dir}")
        
        self.run_phase1()
        self.run_phase2()
        self.run_phase3()
        self.run_phase4()
        self.run_phase5()
        
        # Print summary of all outputs
        print("\n" + "=" * 70)
        print("🎉 DOCUMENTATION PIPELINE COMPLETE!")
        print("=" * 70)
        print("\n📂 All Output Locations:")
        print(f"\n  Phase 1 (Analysis):")
        if "phase1" in self.results and "artifacts" in self.results["phase1"]:
            for key, path in self.results["phase1"]["artifacts"].items():
                print(f"    • {key}: {path}")
        
        print(f"\n  Phase 2 (Docstrings):")
        if "phase2" in self.results and "output_path" in self.results["phase2"]:
            print(f"    • docstrings: {self.results['phase2']['output_path']}")
            print(f"    • cache: {self.cache_dir}")
        
        print(f"\n  Phase 3 (README):")
        if "phase3" in self.results and "readme_path" in self.results["phase3"]:
            print(f"    • README: {self.results['phase3']['readme_path']}")
        
        print(f"\n  Phase 4 (Validation):")
        print(f"    • (in-memory only, no file output)")
        
        print(f"\n  Phase 5 (Evaluation):")
        if "phase5" in self.results and "report_path" in self.results["phase5"]:
            print(f"    • report: {self.results['phase5']['report_path']}")
        
        print("\n" + "=" * 70)
        print(f"💡 See ALL_OUTPUTS_GUIDE.md for detailed information about each output")
        print("=" * 70 + "\n")
        
        return self.results
    
    def cleanup(self):
        """Clean up resources."""
        if self.llm_client:
            self.llm_client.cleanup()
