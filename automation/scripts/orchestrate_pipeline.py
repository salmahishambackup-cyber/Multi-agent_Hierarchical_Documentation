#!/usr/bin/env python3
"""
ORCHESTRATOR: End-to-End Pipeline Automation

This is the MAIN ENTRY POINT.
Coordinates:
1. Stage 1 execution (local)
2. Upload to Google Drive
3. Stage 2 execution (Colab)
4. Download results

Single command: python orchestrate_pipeline.py

Usage:
    python orchestrate_pipeline.py                  # Full pipeline
    python orchestrate_pipeline.py --stage1-only    # Only run Stage 1
    python orchestrate_pipeline.py --stage2-only    # Only run Stage 2 (assumes inputs on Drive)
    python orchestrate_pipeline.py --download-only  # Download existing results
"""

import sys
import json
import time
import logging
import argparse
from pathlib import Path
from typing import Dict, Tuple, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(name)s] - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automation_pipeline.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """Orchestrates the complete end-to-end pipeline."""
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.automation_dir = workspace_root / "automation"
        self.scripts_dir = self.automation_dir / "scripts"
        self.config_dir = self.automation_dir / "config"
        self.logs_dir = self.automation_dir / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        
        # Token for Drive
        self.token_file = self.config_dir / "token.json"
        
        # Execution state
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.execution_log = {
            "pipeline_start": self.timestamp,
            "stages": {}
        }
    
    def run_full_pipeline(self) -> bool:
        """Execute complete pipeline: Stage 1 -> Upload -> Stage 2 -> Download."""
        
        logger.info("="*80)
        logger.info("GENAI PIPELINE - FULL EXECUTION")
        logger.info("="*80)
        
        try:
            # Step 1: Verify authentication
            logger.info("\n[STEP 1/5] Verifying Google Drive authentication...")
            if not self._verify_authentication():
                logger.error("Authentication verification failed. Run: python auth_setup.py")
                return False
            
            # Step 2: Run Stage 1
            logger.info("\n[STEP 2/5] Executing Stage 1 (Repository Analysis)...")
            stage1_result = self._run_stage1()
            if not stage1_result:
                logger.error("Stage 1 failed")
                return False
            
            # Step 3: Upload to Drive
            logger.info("\n[STEP 3/5] Uploading Stage 1 output to Google Drive...")
            stage1_package = stage1_result["package_path"]
            drive_path = self._upload_to_drive(stage1_package)
            if not drive_path:
                logger.error("Upload to Drive failed")
                return False
            
            # Step 4: Run Stage 2 on Colab
            logger.info("\n[STEP 4/5] Triggering Stage 2 execution on Google Colab...")
            if not self._trigger_stage2_on_colab(drive_path):
                logger.error("Stage 2 trigger failed")
                logger.warning("You may need to monitor Colab manually.")
                # Don't fail here - Stage 2 may still complete
            
            # Step 5: Download results (with polling)
            logger.info("\n[STEP 5/5] Downloading Stage 2 results from Google Drive...")
            if self._download_from_drive():
                logger.info("\n" + "="*80)
                logger.info("✅ PIPELINE COMPLETED SUCCESSFULLY!")
                logger.info("="*80)
                return True
            else:
                logger.warning("Download failed or results not ready. Check Drive manually.")
                return False
            
        except Exception as e:
            logger.error(f"❌ Pipeline failed with exception: {e}", exc_info=True)
            return False
    
    def run_stage1_only(self) -> bool:
        """Run only Stage 1 and upload to Drive."""
        
        logger.info("="*80)
        logger.info("STAGE 1 ONLY - Repository Analysis")
        logger.info("="*80)
        
        try:
            logger.info("\n[STEP 1/3] Verifying Google Drive authentication...")
            if not self._verify_authentication():
                logger.error("Authentication verification failed")
                return False
            
            logger.info("\n[STEP 2/3] Executing Stage 1...")
            stage1_result = self._run_stage1()
            if not stage1_result:
                return False
            
            logger.info("\n[STEP 3/3] Uploading to Google Drive...")
            stage1_package = stage1_result["package_path"]
            drive_path = self._upload_to_drive(stage1_package)
            
            if drive_path:
                logger.info(f"\n✅ Stage 1 complete! Outputs on Drive at: {drive_path}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Stage 1 failed: {e}", exc_info=True)
            return False
    
    def run_stage2_only(self) -> bool:
        """Trigger Stage 2 assuming inputs are already on Drive."""
        
        logger.info("="*80)
        logger.info("STAGE 2 ONLY - Documentation Generation")
        logger.info("="*80)
        
        try:
            logger.info("\n[STEP 1/2] Verifying Google Drive authentication...")
            if not self._verify_authentication():
                return False
            
            logger.info("\n[STEP 2/2] Triggering Stage 2 on Colab...")
            # Get most recent stage1 output from Drive
            drive_path = "GenAI_Pipeline_Automation/stage2_inputs"
            
            if self._trigger_stage2_on_colab(drive_path):
                logger.info(f"\n✅ Stage 2 triggered! Monitor progress on Colab.")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Stage 2 trigger failed: {e}", exc_info=True)
            return False
    
    def download_only(self) -> bool:
        """Download existing Stage 2 results from Drive."""
        
        logger.info("="*80)
        logger.info("DOWNLOAD ONLY - Fetch Stage 2 Results")
        logger.info("="*80)
        
        try:
            logger.info("\n[STEP 1/2] Verifying Google Drive authentication...")
            if not self._verify_authentication():
                return False
            
            logger.info("\n[STEP 2/2] Downloading results...")
            if self._download_from_drive():
                logger.info(f"\n✅ Download complete!")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Download failed: {e}", exc_info=True)
            return False
    
    # ===== INTERNAL METHODS =====
    
    def _verify_authentication(self) -> bool:
        """Verify Google Drive token exists and is valid."""
        if not self.token_file.exists():
            logger.error(f"Token file not found: {self.token_file}")
            logger.error("Run: python scripts/auth_setup.py")
            return False
        
        try:
            # Quick verification
            import json
            with open(self.token_file) as f:
                data = json.load(f)
            
            if 'token' not in data or 'refresh_token' not in data:
                logger.error("Token file is invalid")
                return False
            
            logger.info("✓ Google Drive authentication verified")
            return True
            
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            return False
    
    def _run_stage1(self) -> Optional[Dict]:
        """Execute Stage 1 pipeline."""
        try:
            # Import here to avoid issues if dependencies missing
            sys.path.insert(0, str(self.scripts_dir))
            from stage1_runner import Stage1Runner
            
            runner = Stage1Runner(self.workspace_root)
            success, result = runner.run()
            
            if success:
                self.execution_log["stages"]["stage1"] = result['log']
                return result
            else:
                self.execution_log["stages"]["stage1"] = result['log']
                return None
                
        except Exception as e:
            logger.error(f"Failed to run Stage 1: {e}", exc_info=True)
            return None
    
    def _upload_to_drive(self, stage1_package: Path) -> Optional[str]:
        """Upload Stage 1 output to Google Drive."""
        try:
            sys.path.insert(0, str(self.scripts_dir))
            from drive_manager import GoogleDriveManager
            
            manager = GoogleDriveManager(self.token_file)
            manager.ensure_root_folder()
            
            drive_path = manager.upload_stage1_output(stage1_package, self.timestamp)
            logger.info(f"✓ Upload successful: {drive_path}")
            
            self.execution_log["stages"]["upload"] = {
                "status": "success",
                "drive_path": drive_path
            }
            
            return drive_path
            
        except Exception as e:
            logger.error(f"Upload to Drive failed: {e}", exc_info=True)
            self.execution_log["stages"]["upload"] = {"status": "failed", "error": str(e)}
            return None
    
    def _trigger_stage2_on_colab(self, stage1_outputs_path: str) -> bool:
        """Trigger Stage 2 execution on Google Colab."""
        try:
            # For now, provide manual instructions
            # In production, use Colab API
            
            logger.info("\n" + "-"*80)
            logger.info("COLAB EXECUTION INSTRUCTIONS")
            logger.info("-"*80)
            logger.info("\nStage 1 outputs are now on Google Drive at:")
            logger.info(f"  📁 {stage1_outputs_path}")
            logger.info("\nTo automatically run Stage 2:")
            logger.info("  1. Check automation/colab/GenAI_Pipeline_Stage2.ipynb")
            logger.info("  2. Open in Google Colab")
            logger.info("  3. Enable GPU runtime (Runtime > Change runtime type > GPU)")
            logger.info("  4. Run all cells (Ctrl+F9 or Runtime > Run all)")
            logger.info("\nAlternatively, run from Python:")
            logger.info("  python scripts/colab_executor.py")
            logger.info("-"*80 + "\n")
            
            # Try to use colab executor if available
            try:
                sys.path.insert(0, str(self.scripts_dir))
                from colab_executor import ColabExecutor
                
                executor = ColabExecutor(self.token_file)
                return executor.trigger_notebook_execution()
                
            except ImportError:
                logger.warning("Colab executor not available - please run Colab manually")
                return False
            
        except Exception as e:
            logger.error(f"Failed to trigger Stage 2: {e}")
            return False
    
    def _download_from_drive(self, max_wait_minutes: int = 120) -> bool:
        """Download Stage 2 results from Drive."""
        try:
            sys.path.insert(0, str(self.scripts_dir))
            from drive_manager import GoogleDriveManager
            
            manager = GoogleDriveManager(self.token_file)
            
            # Download to local output directory
            output_dir = self.workspace_root / "pipeline_outputs" / self.timestamp
            
            success = manager.download_stage2_output(
                output_folder_name="stage2_outputs",
                download_path=output_dir
            )
            
            if success:
                logger.info(f"✓ Results downloaded to: {output_dir}")
                self.execution_log["stages"]["download"] = {
                    "status": "success",
                    "local_path": str(output_dir)
                }
                return True
            else:
                logger.warning("Stage 2 outputs not found on Drive yet")
                logger.info("Results may still be processing on Colab")
                return False
                
        except Exception as e:
            logger.error(f"Download from Drive failed: {e}", exc_info=True)
            self.execution_log["stages"]["download"] = {"status": "failed", "error": str(e)}
            return False
    
    def save_execution_log(self):
        """Save execution log to file."""
        self.execution_log["pipeline_end"] = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        log_file = self.logs_dir / f"execution_{self.timestamp}.json"
        with open(log_file, 'w') as f:
            json.dump(self.execution_log, f, indent=2)
        
        logger.info(f"Execution log saved to: {log_file}")


def main():
    """Main entry point."""
    
    parser = argparse.ArgumentParser(
        description="GenAI Multi-Stage Pipeline Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python orchestrate_pipeline.py              # Full pipeline
  python orchestrate_pipeline.py --stage1-only  # Only Stage 1
  python orchestrate_pipeline.py --stage2-only  # Only Stage 2
  python orchestrate_pipeline.py --download-only  # Download results
        """
    )
    
    parser.add_argument(
        "--stage1-only",
        action="store_true",
        help="Run Stage 1 only (local analysis + upload)"
    )
    parser.add_argument(
        "--stage2-only",
        action="store_true",
        help="Trigger Stage 2 only (assumes inputs on Drive)"
    )
    parser.add_argument(
        "--download-only",
        action="store_true",
        help="Download Stage 2 results only"
    )
    
    args = parser.parse_args()
    
    # Get workspace root
    workspace_root = Path(__file__).parent.parent.parent
    
    orchestrator = PipelineOrchestrator(workspace_root)
    
    # Execute based on arguments
    if args.stage1_only:
        success = orchestrator.run_stage1_only()
    elif args.stage2_only:
        success = orchestrator.run_stage2_only()
    elif args.download_only:
        success = orchestrator.download_only()
    else:
        success = orchestrator.run_full_pipeline()
    
    # Save execution log
    orchestrator.save_execution_log()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
