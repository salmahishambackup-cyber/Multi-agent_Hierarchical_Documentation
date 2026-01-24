"""
Chat assistant for interactive documentation generation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional
import json

from chat.commands import CommandParser
from pipeline.orchestrator import Orchestrator
from utils import read_json


class Assistant:
    """
    Interactive chat assistant for documentation generation.
    """
    
    def __init__(
        self,
        model_id: str = "Qwen/Qwen2.5-Coder-1.5B-Instruct",
        device: str = "auto",
        quantize: bool = True,
    ):
        """
        Initialize assistant.
        
        Args:
            model_id: HuggingFace model ID
            device: Device (auto/cpu/cuda)
            quantize: Use 4-bit quantization
        """
        self.model_id = model_id
        self.device = device
        self.quantize = quantize
        self.orchestrator: Optional[Orchestrator] = None
        self.parser = CommandParser()
    
    def start(self):
        """Start the chat interface."""
        print("\n" + "="*60)
        print("🤖 Documentation Assistant (Colab T4 Optimized)")
        print("="*60)
        print("\nType 'help' for available commands or 'exit' to quit.")
        
        while True:
            try:
                user_input = input("\n> ").strip()
                
                if not user_input:
                    continue
                
                # Parse command
                parsed = self.parser.parse(user_input)
                command = parsed["command"]
                
                # Handle exit
                if command == "exit":
                    print("\nGoodbye! 👋")
                    if self.orchestrator:
                        self.orchestrator.cleanup()
                    break
                
                # Handle help
                if command == "help":
                    print(self.parser.get_help())
                    continue
                
                # Handle status
                if command == "status":
                    self._show_status()
                    continue
                
                # Handle show readme
                if command == "show_readme":
                    self._show_readme()
                    continue
                
                # Handle show report
                if command == "show_report":
                    self._show_report()
                    continue
                
                # Handle document (full pipeline)
                if command == "document":
                    self._run_full_pipeline(parsed.get("path"))
                    continue
                
                # Handle individual phases
                if command == "phase1":
                    self._run_phase1(parsed.get("path"))
                    continue
                
                if command == "phase2":
                    self._run_phase2()
                    continue
                
                if command == "phase3":
                    self._run_phase3()
                    continue
                
                if command == "phase4":
                    self._run_phase4()
                    continue
                
                if command == "phase5":
                    self._run_phase5()
                    continue
                
                # Unknown command
                if command == "unknown":
                    print("❓ I didn't understand that. Type 'help' for available commands.")
                    print(f"   Or try: 'document <path>' to generate documentation")
                
            except KeyboardInterrupt:
                print("\n\nInterrupted. Type 'exit' to quit.")
            except Exception as e:
                print(f"\n❌ Error: {e}")
    
    def _ensure_orchestrator(self, repo_path: str) -> bool:
        """Ensure orchestrator is initialized."""
        if not repo_path:
            print("📂 Enter project path: ", end="")
            repo_path = input().strip()
        
        if not repo_path:
            print("❌ Project path required")
            return False
        
        # Convert to absolute path
        repo_path = Path(repo_path).resolve()
        
        if not repo_path.exists():
            print(f"❌ Path does not exist: {repo_path}")
            return False
        
        if not repo_path.is_dir():
            print(f"❌ Path is not a directory: {repo_path}")
            return False
        
        # Initialize orchestrator if not already done or path changed
        if self.orchestrator is None or self.orchestrator.repo_path != repo_path:
            print(f"\n📂 Initializing for: {repo_path.name}")
            self.orchestrator = Orchestrator(
                repo_path=str(repo_path),
                model_id=self.model_id,
                device=self.device,
                quantize=self.quantize,
            )
        
        return True
    
    def _run_full_pipeline(self, repo_path: Optional[str]):
        """Run full documentation pipeline."""
        if not self._ensure_orchestrator(repo_path):
            return
        
        try:
            self.orchestrator.run_all()
        except Exception as e:
            print(f"❌ Pipeline failed: {e}")
    
    def _run_phase1(self, repo_path: Optional[str]):
        """Run Phase 1: Analysis."""
        if not self._ensure_orchestrator(repo_path):
            return
        
        try:
            self.orchestrator.run_phase1()
        except Exception as e:
            print(f"❌ Phase 1 failed: {e}")
    
    def _run_phase2(self):
        """Run Phase 2: Docstrings."""
        if self.orchestrator is None:
            print("❌ Run Phase 1 (analyze) first")
            return
        
        try:
            self.orchestrator.run_phase2()
        except Exception as e:
            print(f"❌ Phase 2 failed: {e}")
    
    def _run_phase3(self):
        """Run Phase 3: README."""
        if self.orchestrator is None:
            print("❌ Run Phase 1 (analyze) first")
            return
        
        try:
            self.orchestrator.run_phase3()
        except Exception as e:
            print(f"❌ Phase 3 failed: {e}")
    
    def _run_phase4(self):
        """Run Phase 4: Validation."""
        if self.orchestrator is None:
            print("❌ Run Phase 3 (generate readme) first")
            return
        
        try:
            self.orchestrator.run_phase4()
        except Exception as e:
            print(f"❌ Phase 4 failed: {e}")
    
    def _run_phase5(self):
        """Run Phase 5: Evaluation."""
        if self.orchestrator is None:
            print("❌ Run Phase 3 (generate readme) first")
            return
        
        try:
            self.orchestrator.run_phase5()
        except Exception as e:
            print(f"❌ Phase 5 failed: {e}")
    
    def _show_status(self):
        """Show current pipeline status."""
        if self.orchestrator is None:
            print("\n📊 Status: Not initialized")
            print("   Run 'document <path>' or 'analyze <path>' to start")
            return
        
        print(f"\n📊 Status:")
        print(f"   Project: {self.orchestrator.project_name}")
        print(f"   Path: {self.orchestrator.repo_path}")
        print(f"\n   Completed phases:")
        
        for phase in ["phase1", "phase2", "phase3", "phase4", "phase5"]:
            if phase in self.orchestrator.results:
                phase_num = phase[-1]
                print(f"   ✅ Phase {phase_num}")
            else:
                phase_num = phase[-1]
                print(f"   ⬜ Phase {phase_num}")
    
    def _show_readme(self):
        """Display generated README."""
        if self.orchestrator is None or "phase3" not in self.orchestrator.results:
            print("❌ README not generated yet. Run 'generate readme' first.")
            return
        
        readme_path = self.orchestrator.results["phase3"]["readme_path"]
        
        try:
            content = Path(readme_path).read_text()
            print("\n" + "="*60)
            print("📄 README.md")
            print("="*60)
            print(content)
            print("="*60)
        except Exception as e:
            print(f"❌ Could not read README: {e}")
    
    def _show_report(self):
        """Display evaluation report."""
        if self.orchestrator is None or "phase5" not in self.orchestrator.results:
            print("❌ Evaluation not done yet. Run 'evaluate' first.")
            return
        
        report_path = self.orchestrator.results["phase5"]["report_path"]
        
        try:
            report = read_json(report_path)
            print("\n" + "="*60)
            print("📊 Evaluation Report")
            print("="*60)
            print(json.dumps(report, indent=2))
            print("="*60)
        except Exception as e:
            print(f"❌ Could not read report: {e}")
