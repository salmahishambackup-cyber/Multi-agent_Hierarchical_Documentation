#!/usr/bin/env python3
"""
STAGE 1: Repository Analysis & Module Decomposition

Runs locally on Windows.
Produces structured outputs (AST, components, dependencies).
"""

import sys
import os
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Tuple
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Stage1Runner:
    """Orchestrates Stage 1 (Repository Analysis)."""
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.proj_genai_root = workspace_root / "proj-GenAI"
        self.stage1_output_dir = self.proj_genai_root / "src" / "data" / "artifacts"
        self.artifacts_to_transfer = ["ast", "components", "dependencies"]
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.execution_log = {
            "stage": "stage1",
            "timestamp": self.timestamp,
            "status": None,
            "errors": []
        }
    
    def run(self) -> Tuple[bool, Dict]:
        """
        Execute Stage 1 pipeline.
        
        Returns:
            (success: bool, result: Dict with paths and metadata)
        """
        logger.info("="*70)
        logger.info("STAGE 1: Repository Analysis & Module Decomposition")
        logger.info("="*70)
        
        try:
            # Verify proj-GenAI structure
            logger.info("Step 1/4: Verifying proj-GenAI structure...")
            if not self._verify_structure():
                raise RuntimeError("proj-GenAI structure validation failed")
            
            # Execute Stage 1 pipeline
            logger.info("Step 2/4: Executing Stage 1 pipeline...")
            if not self._execute_pipeline():
                raise RuntimeError("Stage 1 pipeline execution failed")
            
            # Verify outputs
            logger.info("Step 3/4: Verifying Stage 1 outputs...")
            output_manifest = self._verify_outputs()
            if not output_manifest:
                raise RuntimeError("Output verification failed")
            
            # Package for transfer
            logger.info("Step 4/4: Preparing outputs for transfer...")
            package_path = self._prepare_transfer()
            
            self.execution_log["status"] = "success"
            self.execution_log["output_package"] = str(package_path)
            self.execution_log["manifest"] = output_manifest
            
            logger.info(f"\n✅ Stage 1 completed successfully!")
            logger.info(f"Output package: {package_path}")
            logger.info(f"Package size: {self._get_dir_size(package_path) / (1024*1024):.2f} MB")
            
            return True, {
                "package_path": package_path,
                "manifest": output_manifest,
                "log": self.execution_log
            }
            
        except Exception as e:
            logger.error(f"❌ Stage 1 failed: {e}")
            self.execution_log["status"] = "failed"
            self.execution_log["error"] = str(e)
            return False, {"error": str(e), "log": self.execution_log}
    
    def _verify_structure(self) -> bool:
        """Verify proj-GenAI has required structure."""
        required_paths = [
            self.proj_genai_root / "src" / "main.py",
            self.proj_genai_root / "src" / "pipeline" / "orchestrator.py",
            self.stage1_output_dir
        ]
        
        for path in required_paths:
            if not path.exists():
                logger.error(f"Missing: {path}")
                return False
        
        logger.info(f"✓ proj-GenAI structure verified")
        return True
    
    def _execute_pipeline(self) -> bool:
        """Execute proj-GenAI/src/main.py."""
        try:
            main_script = self.proj_genai_root / "src" / "main.py"
            
            # Add proj-GenAI/src to PYTHONPATH
            env = os.environ.copy()
            env['PYTHONPATH'] = str(self.proj_genai_root / "src") + ":" + env.get('PYTHONPATH', '')
            
            logger.info(f"Executing: {main_script}")
            result = subprocess.run(
                [sys.executable, str(main_script)],
                cwd=str(self.proj_genai_root / "src"),
                env=env,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes
            )
            
            if result.returncode != 0:
                logger.error(f"Stage 1 script failed:")
                logger.error(f"STDOUT: {result.stdout}")
                logger.error(f"STDERR: {result.stderr}")
                self.execution_log["errors"].append({
                    "step": "execute_pipeline",
                    "stdout": result.stdout,
                    "stderr": result.stderr
                })
                return False
            
            logger.info(f"✓ Pipeline executed successfully")
            self.execution_log["pipeline_output"] = result.stdout
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("Pipeline execution timed out (>600s)")
            return False
        except Exception as e:
            logger.error(f"Pipeline execution error: {e}")
            return False
    
    def _verify_outputs(self) -> Dict:
        """Verify that Stage 1 produced expected outputs."""
        manifest = {}
        
        for artifact_type in self.artifacts_to_transfer:
            artifact_path = self.stage1_output_dir / artifact_type
            
            if not artifact_path.exists():
                logger.warning(f"Missing artifact: {artifact_type}")
                continue
            
            files = list(artifact_path.glob("**/*"))
            file_count = len([f for f in files if f.is_file()])
            dir_size = self._get_dir_size(artifact_path)
            
            manifest[artifact_type] = {
                "path": str(artifact_path),
                "file_count": file_count,
                "size_bytes": dir_size,
                "size_mb": dir_size / (1024*1024)
            }
            
            logger.info(f"✓ {artifact_type}: {file_count} files, {dir_size / (1024*1024):.2f} MB")
        
        if not manifest:
            logger.error("No output artifacts found")
            return None
        
        return manifest
    
    def _prepare_transfer(self) -> Path:
        """
        Prepare outputs for transfer to Colab.
        Creates a timestamped package directory.
        """
        package_dir = self.stage1_output_dir.parent / f"transfer_{self.timestamp}"
        package_dir.mkdir(exist_ok=True)
        
        logger.info(f"Preparing package at: {package_dir}")
        
        for artifact_type in self.artifacts_to_transfer:
            src = self.stage1_output_dir / artifact_type
            dst = package_dir / artifact_type
            
            if src.exists():
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
                logger.info(f"✓ Copied {artifact_type}")
        
        return package_dir
    
    @staticmethod
    def _get_dir_size(path: Path) -> int:
        """Get total size of directory in bytes."""
        total = 0
        for entry in path.rglob('*'):
            if entry.is_file():
                total += entry.stat().st_size
        return total


def main():
    """Main entry point."""
    import os
    
    # Get workspace root
    workspace_root = Path(__file__).parent.parent.parent
    
    runner = Stage1Runner(workspace_root)
    success, result = runner.run()
    
    # Save execution log
    log_file = workspace_root / "automation" / "logs" / f"stage1_{result['log']['timestamp']}.json"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_file, 'w') as f:
        json.dump(result['log'], f, indent=2)
    
    logger.info(f"Log saved to: {log_file}")
    
    if not success:
        sys.exit(1)
    
    print("\n" + "="*70)
    print("STAGE 1 OUTPUT SUMMARY")
    print("="*70)
    print(json.dumps(result['manifest'], indent=2))
    print(f"\nPackage location: {result['package_path']}")
    
    sys.exit(0)


if __name__ == "__main__":
    main()
