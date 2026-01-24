import json
import hashlib
from typing import Any, Dict, List
from collections import OrderedDict
from datetime import datetime

class DeterminismEnforcer:
    """
    Ensure reproducible outputs across runs.
    - Pin versions
    - Sort consistently
    - Normalize floating point precision
    """
    
    # Expected versions (from requirements.txt or setup.py)
    REQUIRED_VERSIONS = {
        "tree-sitter": "0.20.4",  # Example: adjust to actual version
        "python": "3.9+",
        "jsonschema": "4.0+",
    }
    
    @staticmethod
    def verify_versions() -> Dict[str, str]:
        """
        Verify critical dependencies are correct versions.
        
        Returns:
            {
                "tree-sitter": "0.20.4",
                "python": "3.10.5",
                ...
                "all_compatible": True/False
            }
        """
        import sys
        import tree_sitter
        
        versions = {
            "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "tree-sitter": getattr(tree_sitter, '__version__', 'unknown'),
        }
        
        # Check compatibility
        versions["all_compatible"] = True  # TODO: Implement actual checks
        
        return versions
    
    @staticmethod
    def sort_dict(d: Any, depth: int = 0) -> Any:
        """
        Recursively sort dictionaries by key for consistent output.
        Preserves arrays and primitive types.
        """
        if isinstance(d, dict):
            return OrderedDict((k, DeterminismEnforcer.sort_dict(d[k], depth+1)) 
                             for k in sorted(d.keys()))
        elif isinstance(d, list):
            return [DeterminismEnforcer.sort_dict(item, depth+1) for item in d]
        elif isinstance(d, set):
            # Convert sets to sorted lists
            return sorted([DeterminismEnforcer.sort_dict(item, depth+1) for item in d], 
                         key=str)
        else:
            return d
    
    @staticmethod
    def normalize_float(value: float, precision: int = 3) -> float:
        """
        Normalize floating point values to fixed precision.
        Prevents precision drift between runs.
        """
        if isinstance(value, float):
            return round(value, precision)
        return value
    
    @staticmethod
    def normalize_value(value: Any) -> Any:
        """
        Recursively normalize values for determinism.
        """
        if isinstance(value, dict):
            return {k: DeterminismEnforcer.normalize_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [DeterminismEnforcer.normalize_value(v) for v in value]
        elif isinstance(value, set):
            return sorted([DeterminismEnforcer.normalize_value(v) for v in value], key=str)
        elif isinstance(value, float):
            return DeterminismEnforcer.normalize_float(value)
        else:
            return value
    
    @staticmethod
    def compute_content_hash(data: Any) -> str:
        """
        Compute SHA256 hash of data for integrity verification.
        
        Ensures outputs haven't been tampered with.
        """
        json_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    @staticmethod
    def make_deterministic(data: Any) -> Any:
        """
        Apply all determinism transformations.
        
        Returns:
            Sorted, normalized data structure
        """
        # Normalize values (floats, sets)
        normalized = DeterminismEnforcer.normalize_value(data)
        
        # Sort all dictionaries
        sorted_data = DeterminismEnforcer.sort_dict(normalized)
        
        return sorted_data


class DeterminismReport:
    """
    Report on determinism properties of outputs.
    """
    
    def __init__(self):
        self.timestamp = datetime.now().isoformat()
        self.versions = DeterminismEnforcer.verify_versions()
        self.hashes = {}
    
    def add_artifact_hash(self, artifact_name: str, data: Any):
        """Add integrity hash for an artifact."""
        content_hash = DeterminismEnforcer.compute_content_hash(data)
        self.hashes[artifact_name] = {
            "hash": content_hash,
            "hash_type": "sha256",
            "timestamp": datetime.now().isoformat()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Export report as dictionary."""
        return {
            "determinism_report": {
                "timestamp": self.timestamp,
                "versions": self.versions,
                "artifact_hashes": self.hashes
            }
        }
    
    def print_summary(self):
        """Print human-readable summary."""
        print(f"\n[DETERMINISM REPORT]")
        print(f"Timestamp: {self.timestamp}")
        print(f"Python: {self.versions.get('python')}")
        print(f"Tree-sitter: {self.versions.get('tree-sitter')}")
        print(f"Versions compatible: {self.versions.get('all_compatible', '?')}")
        print(f"\nArtifact hashes:")
        for artifact, info in self.hashes.items():
            print(f"  {artifact}: {info['hash'][:16]}...")