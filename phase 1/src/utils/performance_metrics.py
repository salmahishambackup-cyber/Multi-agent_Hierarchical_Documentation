"""
Performance Metrics & Optimization Logging
Tracks execution time, memory usage, and provides optimization insights.
"""

import time
import psutil
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict


class PerformanceTimer:
    """Context manager for timing code blocks."""
    
    def __init__(self, stage_name: str):
        self.stage_name = stage_name
        self.start_time = None
        self.end_time = None
        self.duration = 0.0
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        return False


class MemoryTracker:
    """Tracks memory usage for a process."""
    
    @staticmethod
    def get_current_usage() -> Dict[str, float]:
        """Get current memory usage in MB."""
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        
        return {
            "rss_mb": mem_info.rss / (1024 * 1024),  # Resident Set Size
            "vms_mb": mem_info.vms / (1024 * 1024),  # Virtual Memory Size
        }
    
    @staticmethod
    def get_peak_usage() -> Dict[str, float]:
        """Get peak memory usage during execution."""
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        
        return {
            "peak_rss_mb": mem_info.rss / (1024 * 1024),
        }


class StageMetrics:
    """Metrics for a single pipeline stage."""
    
    def __init__(self, stage_name: str):
        self.stage_name = stage_name
        self.start_time = None
        self.end_time = None
        self.duration = 0.0
        self.start_memory = None
        self.end_memory = None
        self.memory_delta = 0.0
        self.items_processed = 0
        self.custom_metrics = {}
    
    def record_start(self):
        """Record start time and memory."""
        self.start_time = time.time()
        self.start_memory = MemoryTracker.get_current_usage()
    
    def record_end(self):
        """Record end time and memory."""
        self.end_time = time.time()
        self.end_memory = MemoryTracker.get_current_usage()
        self.duration = self.end_time - self.start_time
        self.memory_delta = self.end_memory["rss_mb"] - self.start_memory["rss_mb"]
    
    def add_custom_metric(self, key: str, value: Any):
        """Add custom metric for this stage."""
        self.custom_metrics[key] = value
    
    def get_throughput(self) -> float:
        """Calculate items per second."""
        if self.duration > 0 and self.items_processed > 0:
            return self.items_processed / self.duration
        return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "stage": self.stage_name,
            "duration_sec": round(self.duration, 3),
            "memory_delta_mb": round(self.memory_delta, 2),
            "items_processed": self.items_processed,
            "throughput_items_per_sec": round(self.get_throughput(), 2),
            "custom_metrics": self.custom_metrics
        }


class PerformanceMonitor:
    """Monitors and aggregates performance metrics across pipeline stages."""
    
    def __init__(self):
        self.stages: Dict[str, StageMetrics] = {}
        self.execution_start = None
        self.execution_end = None
        self.total_duration = 0.0
        self.initial_memory = None
        self.final_memory = None
        self.total_memory_used = 0.0
    
    def start_monitoring(self):
        """Start overall monitoring."""
        self.execution_start = time.time()
        self.initial_memory = MemoryTracker.get_current_usage()
    
    def end_monitoring(self):
        """End overall monitoring."""
        self.execution_end = time.time()
        self.final_memory = MemoryTracker.get_current_usage()
        self.total_duration = self.execution_end - self.execution_start
        self.total_memory_used = self.final_memory["rss_mb"] - self.initial_memory["rss_mb"]
    
    def start_stage(self, stage_name: str) -> StageMetrics:
        """Start tracking a pipeline stage."""
        if stage_name not in self.stages:
            self.stages[stage_name] = StageMetrics(stage_name)
        
        metrics = self.stages[stage_name]
        metrics.record_start()
        return metrics
    
    def end_stage(self, stage_name: str, items_processed: int = 0, **custom_metrics):
        """End tracking a pipeline stage."""
        if stage_name in self.stages:
            metrics = self.stages[stage_name]
            metrics.record_end()
            metrics.items_processed = items_processed
            for key, value in custom_metrics.items():
                metrics.add_custom_metric(key, value)
    
    def get_slowest_stages(self, top_n: int = 5) -> List[Dict[str, Any]]:
        """Get slowest stages."""
        sorted_stages = sorted(
            self.stages.values(),
            key=lambda m: m.duration,
            reverse=True
        )
        return [stage.to_dict() for stage in sorted_stages[:top_n]]
    
    def get_most_memory_intensive_stages(self, top_n: int = 5) -> List[Dict[str, Any]]:
        """Get stages with largest memory delta."""
        sorted_stages = sorted(
            self.stages.values(),
            key=lambda m: abs(m.memory_delta),
            reverse=True
        )
        return [stage.to_dict() for stage in sorted_stages[:top_n]]
    
    def identify_bottlenecks(self) -> List[Dict[str, Any]]:
        """Identify performance bottlenecks."""
        bottlenecks = []
        
        # Find stages taking >30% of total time
        threshold_time = self.total_duration * 0.3
        for stage in self.stages.values():
            if stage.duration > threshold_time:
                bottlenecks.append({
                    "stage": stage.stage_name,
                    "type": "slow",
                    "duration_sec": round(stage.duration, 3),
                    "percentage_of_total": round((stage.duration / self.total_duration) * 100, 1),
                    "recommendation": f"Optimize {stage.stage_name} - consider parallelization or caching"
                })
            
            # Find stages with high memory growth
            if stage.memory_delta > 100:  # >100MB growth
                bottlenecks.append({
                    "stage": stage.stage_name,
                    "type": "memory",
                    "memory_delta_mb": round(stage.memory_delta, 2),
                    "recommendation": f"Reduce memory footprint in {stage.stage_name} - consider streaming or chunking"
                })
        
        return bottlenecks
    
    def generate_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive optimization report."""
        bottlenecks = self.identify_bottlenecks()
        
        return {
            "execution_summary": {
                "total_duration_sec": round(self.total_duration, 3),
                "total_memory_used_mb": round(self.total_memory_used, 2),
                "initial_memory_mb": round(self.initial_memory["rss_mb"], 2),
                "final_memory_mb": round(self.final_memory["rss_mb"], 2),
                "timestamp": datetime.now().isoformat()
            },
            "stage_metrics": [stage.to_dict() for stage in self.stages.values()],
            "slowest_stages": self.get_slowest_stages(5),
            "most_memory_intensive": self.get_most_memory_intensive_stages(5),
            "bottlenecks": bottlenecks,
            "recommendations": self._generate_recommendations(bottlenecks)
        }
    
    def _generate_recommendations(self, bottlenecks: List[Dict]) -> List[str]:
        """Generate optimization recommendations based on bottlenecks."""
        recommendations = []
        
        if not bottlenecks:
            recommendations.append("✓ Pipeline performance is well-balanced")
            return recommendations
        
        slow_stages = [b for b in bottlenecks if b["type"] == "slow"]
        memory_stages = [b for b in bottlenecks if b["type"] == "memory"]
        
        if slow_stages:
            recommendations.append(
                f"⚠ {len(slow_stages)} slow stage(s) detected - consider parallelization, caching, or algorithm improvements"
            )
        
        if memory_stages:
            recommendations.append(
                f"⚠ {len(memory_stages)} memory-intensive stage(s) detected - consider streaming processing or lazy evaluation"
            )
        
        # Calculate overall efficiency
        total_stage_time = sum(stage.duration for stage in self.stages.values())
        efficiency = (total_stage_time / self.total_duration) * 100
        if efficiency < 70:
            recommendations.append(
                f"ℹ Pipeline efficiency is {efficiency:.0f}% - overhead from I/O or other operations"
            )
        
        return recommendations
    
    def print_summary(self) -> None:
        """Print performance summary to console."""
        print(f"\n[PERFORMANCE METRICS]")
        print(f"Total execution time: {self.total_duration:.3f}s")
        print(f"Memory used: {self.total_memory_used:.2f}MB (peak: {self.final_memory['rss_mb']:.2f}MB)")
        
        print(f"\nStage breakdown:")
        for stage in sorted(self.stages.values(), key=lambda s: s.duration, reverse=True)[:5]:
            print(f"  {stage.stage_name}: {stage.duration:.3f}s ({(stage.duration/self.total_duration)*100:.1f}%)")
            if stage.memory_delta != 0:
                print(f"    Memory: {stage.memory_delta:+.2f}MB")
            throughput = stage.get_throughput()
            if throughput > 0:
                print(f"    Throughput: {throughput:.1f} items/sec")
        
        print(f"\nBottlenecks:")
        bottlenecks = self.identify_bottlenecks()
        if bottlenecks:
            for bn in bottlenecks[:3]:
                if bn["type"] == "slow":
                    print(f"  ⚠ {bn['stage']}: {bn['duration_sec']:.3f}s ({bn['percentage_of_total']:.1f}%)")
                else:
                    print(f"  ⚠ {bn['stage']}: {bn['memory_delta_mb']:+.2f}MB memory")
        else:
            print(f"  ✓ No major bottlenecks detected")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "performance_metrics": self.generate_optimization_report()
        }


class OptimizationLogger:
    """Logs optimization-related insights during execution."""
    
    def __init__(self):
        self.logs: List[Dict[str, Any]] = []
    
    def log_optimization_insight(self, stage: str, insight_type: str, message: str, data: Optional[Dict] = None):
        """Log an optimization insight."""
        self.logs.append({
            "timestamp": datetime.now().isoformat(),
            "stage": stage,
            "type": insight_type,  # "cache_hit", "skip_optimization", "parallelizable", "memory_leak", etc.
            "message": message,
            "data": data or {}
        })
    
    def get_insights_by_type(self, insight_type: str) -> List[Dict]:
        """Get all insights of a specific type."""
        return [log for log in self.logs if log["type"] == insight_type]
    
    def generate_summary(self) -> Dict[str, Any]:
        """Generate optimization insights summary."""
        by_type = defaultdict(int)
        for log in self.logs:
            by_type[log["type"]] += 1
        
        return {
            "total_insights": len(self.logs),
            "by_type": dict(by_type),
            "insights": self.logs[:10]  # First 10 insights
        }
    
    def print_summary(self) -> None:
        """Print optimization insights to console."""
        print(f"\n[OPTIMIZATION INSIGHTS]")
        summary = self.generate_summary()
        
        if summary["total_insights"] == 0:
            print("  ℹ No optimization insights logged")
            return
        
        for insight_type, count in summary["by_type"].items():
            print(f"  {insight_type}: {count}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "optimization_logs": self.generate_summary()
        }
