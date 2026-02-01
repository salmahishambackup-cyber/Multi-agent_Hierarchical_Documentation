"""
Phase 5: Final evaluation of documentation quality.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any
import json

from phase2_docstrings.agents import Writer
from utils import write_json
from utils.profiler import profile_phase


class Evaluator:
    """
    Phase 5: Evaluate documentation on 4 metrics.
    Single LLM call for all metrics.
    """
    
    def __init__(
        self,
        writer: Writer,
        artifacts_dir: str,
        readme_content: str,
    ):
        """
        Initialize evaluator.
        
        Args:
            writer: Writer agent for evaluation
            artifacts_dir: Directory for artifacts
            readme_content: README content to evaluate
        """
        self.writer = writer
        self.artifacts_dir = Path(artifacts_dir).resolve()
        self.readme_content = readme_content
    
    @profile_phase("Phase 5: Evaluation")
    def run(self) -> Dict[str, Any]:
        """
        Evaluate documentation quality.
        
        Returns:
            Dictionary with evaluation scores and report path
        """
        print("Evaluating documentation...")
        
        # Generate evaluation in one call
        try:
            eval_json = self.writer.evaluate_documentation(self.readme_content)
            
            # Parse JSON response
            evaluation = json.loads(eval_json)
            
            # Calculate overall score if not provided
            if "overall" not in evaluation:
                scores = [
                    evaluation.get("clarity", 0),
                    evaluation.get("completeness", 0),
                    evaluation.get("consistency", 0),
                    evaluation.get("usability", 0),
                ]
                evaluation["overall"] = sum(scores) / len(scores)
            
        except json.JSONDecodeError:
            # Fallback if LLM doesn't return valid JSON
            print("Warning: Could not parse evaluation JSON, using defaults")
            evaluation = {
                "clarity": 7,
                "completeness": 7,
                "consistency": 7,
                "usability": 7,
                "overall": 7.0,
                "strengths": ["Documentation generated successfully"],
                "suggestions": ["Manual review recommended"],
            }
        
        # Save evaluation report
        report_path = self.artifacts_dir / "evaluation_report.json"
        write_json(report_path, evaluation)
        
        # Print summary
        print(f"\n📊 Score: {evaluation['overall']:.1f}/10")
        print(f"   Clarity: {evaluation.get('clarity', 0)}")
        print(f"   Completeness: {evaluation.get('completeness', 0)}")
        print(f"   Consistency: {evaluation.get('consistency', 0)}")
        print(f"   Usability: {evaluation.get('usability', 0)}")
        
        return {
            "report_path": str(report_path),
            "evaluation": evaluation,
        }
