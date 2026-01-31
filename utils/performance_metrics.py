"""Performance monitoring utilities."""

import time
import psutil
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class StageMetrics:
    """Metrics for a single stage."""
    stage_name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    memory_start: Optional[float] = None
    memory_end: Optional[float] = None
    memory_delta: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "stage_name": self.stage_name,
            "duration_seconds": round(self.duration, 3) if self.duration else None,
            "memory_delta_mb": round(self.memory_delta, 2) if self.memory_delta else None,
        }


class PerformanceTimer:
    """Simple performance timer."""
    
    def __init__(self):
        self.start_time = time.time()
    
    def elapsed(self) -> float:
        """Get elapsed time in seconds."""
        return time.time() - self.start_time
    
    def reset(self) -> float:
        """Reset timer and return elapsed time."""
        elapsed = self.elapsed()
        self.start_time = time.time()
        return elapsed


class MemoryTracker:
    """Track memory usage."""
    
    @staticmethod
    def get_memory_mb() -> float:
        """Get current memory usage in MB."""
        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)
    
    @staticmethod
    def get_memory_percent() -> float:
        """Get current memory usage as percentage."""
        process = psutil.Process()
        return process.memory_percent()


class PerformanceMonitor:
    """Monitor performance of operations."""
    
    def __init__(self):
        self.stages: List[StageMetrics] = []
        self.current_stage: Optional[StageMetrics] = None
        self.overall_start = time.time()
    
    def start_stage(self, stage_name: str) -> None:
        """Start monitoring a stage."""
        if self.current_stage:
            self.end_stage()
        
        self.current_stage = StageMetrics(
            stage_name=stage_name,
            start_time=time.time(),
            memory_start=MemoryTracker.get_memory_mb()
        )
    
    def end_stage(self) -> Optional[StageMetrics]:
        """End monitoring current stage."""
        if not self.current_stage:
            return None
        
        self.current_stage.end_time = time.time()
        self.current_stage.duration = (
            self.current_stage.end_time - self.current_stage.start_time
        )
        self.current_stage.memory_end = MemoryTracker.get_memory_mb()
        self.current_stage.memory_delta = (
            self.current_stage.memory_end - self.current_stage.memory_start
        )
        
        self.stages.append(self.current_stage)
        completed_stage = self.current_stage
        self.current_stage = None
        
        return completed_stage
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        # End current stage if still running
        if self.current_stage:
            self.end_stage()
        
        overall_duration = time.time() - self.overall_start
        
        return {
            "overall_duration_seconds": round(overall_duration, 3),
            "stages": [stage.to_dict() for stage in self.stages],
            "total_stages": len(self.stages),
        }
    
    def print_summary(self) -> None:
        """Print performance summary."""
        summary = self.get_summary()
        
        print("\n" + "="*60)
        print("PERFORMANCE SUMMARY")
        print("="*60)
        print(f"Overall Duration: {summary['overall_duration_seconds']:.3f}s")
        print(f"Total Stages: {summary['total_stages']}")
        print("\nStage Details:")
        
        for stage in summary['stages']:
            print(f"  • {stage['stage_name']}")
            print(f"    Duration: {stage['duration_seconds']:.3f}s")
            if stage['memory_delta_mb'] is not None:
                print(f"    Memory Δ: {stage['memory_delta_mb']:+.2f} MB")
        
        print("="*60 + "\n")


class OptimizationLogger:
    """Log optimization opportunities."""
    
    def __init__(self):
        self.suggestions: List[str] = []
    
    def suggest(self, message: str) -> None:
        """Add an optimization suggestion."""
        self.suggestions.append(message)
    
    def suggest_if_slow(self, stage_name: str, duration: float, threshold: float = 10.0) -> None:
        """Suggest optimization if stage is slow."""
        if duration > threshold:
            self.suggest(
                f"{stage_name} took {duration:.1f}s (threshold: {threshold}s). "
                f"Consider optimization."
            )
    
    def suggest_if_memory_heavy(self, stage_name: str, memory_mb: float, threshold: float = 500.0) -> None:
        """Suggest optimization if stage uses too much memory."""
        if memory_mb > threshold:
            self.suggest(
                f"{stage_name} used {memory_mb:.1f}MB (threshold: {threshold}MB). "
                f"Consider optimization."
            )
    
    def get_suggestions(self) -> List[str]:
        """Get all suggestions."""
        return self.suggestions
    
    def print_suggestions(self) -> None:
        """Print optimization suggestions."""
        if not self.suggestions:
            return
        
        print("\n" + "="*60)
        print("OPTIMIZATION SUGGESTIONS")
        print("="*60)
        for i, suggestion in enumerate(self.suggestions, 1):
            print(f"{i}. {suggestion}")
        print("="*60 + "\n")
