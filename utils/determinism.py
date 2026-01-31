"""Determinism enforcement utilities."""

import json
from typing import Any, Dict, List, Set
from dataclasses import dataclass, field
from collections import OrderedDict


@dataclass
class DeterminismReport:
    """Report on determinism checks."""
    is_deterministic: bool = True
    issues: List[str] = field(default_factory=list)
    
    def add_issue(self, message: str) -> None:
        """Add a determinism issue."""
        self.is_deterministic = False
        self.issues.append(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_deterministic": self.is_deterministic,
            "issues": self.issues
        }


class DeterminismEnforcer:
    """Enforces deterministic outputs in data structures."""
    
    @staticmethod
    def sort_dict(data: Dict[str, Any]) -> OrderedDict:
        """
        Sort dictionary recursively by keys.
        
        Args:
            data: Dictionary to sort
            
        Returns:
            Sorted OrderedDict
        """
        if not isinstance(data, dict):
            return data
        
        result = OrderedDict()
        for key in sorted(data.keys()):
            value = data[key]
            if isinstance(value, dict):
                result[key] = DeterminismEnforcer.sort_dict(value)
            elif isinstance(value, list):
                result[key] = DeterminismEnforcer.sort_list(value)
            else:
                result[key] = value
        
        return result
    
    @staticmethod
    def sort_list(data: List[Any]) -> List[Any]:
        """
        Sort list elements if they are sortable.
        
        Args:
            data: List to sort
            
        Returns:
            Sorted list
        """
        if not data:
            return data
        
        # Try to sort if elements are comparable
        try:
            if all(isinstance(x, (str, int, float)) for x in data):
                return sorted(data)
            elif all(isinstance(x, dict) for x in data):
                # Sort dicts by a key if available
                if all('id' in x for x in data):
                    return sorted(data, key=lambda x: x['id'])
                elif all('name' in x for x in data):
                    return sorted(data, key=lambda x: x['name'])
                elif all('file' in x for x in data):
                    return sorted(data, key=lambda x: x['file'])
        except (TypeError, KeyError):
            pass
        
        # Return as-is if not sortable
        return data
    
    @staticmethod
    def enforce_determinism(data: Any) -> Any:
        """
        Enforce determinism in data structure.
        
        Args:
            data: Data to make deterministic
            
        Returns:
            Deterministic version of data
        """
        if isinstance(data, dict):
            return DeterminismEnforcer.sort_dict(data)
        elif isinstance(data, list):
            return DeterminismEnforcer.sort_list(data)
        else:
            return data
    
    @staticmethod
    def check_determinism(data1: Any, data2: Any) -> DeterminismReport:
        """
        Check if two data structures are deterministically equal.
        
        Args:
            data1: First data structure
            data2: Second data structure
            
        Returns:
            DeterminismReport
        """
        report = DeterminismReport()
        
        # Convert to JSON strings for comparison
        try:
            json1 = json.dumps(data1, sort_keys=True, indent=2)
            json2 = json.dumps(data2, sort_keys=True, indent=2)
            
            if json1 != json2:
                report.add_issue("Data structures are not equal")
        except Exception as e:
            report.add_issue(f"Failed to compare: {e}")
        
        return report
    
    @staticmethod
    def deduplicate_list(data: List[Any], key: str = None) -> List[Any]:
        """
        Remove duplicates from list while preserving order.
        
        Args:
            data: List to deduplicate
            key: Optional key for dict elements
            
        Returns:
            Deduplicated list
        """
        if not data:
            return data
        
        seen: Set[Any] = set()
        result = []
        
        for item in data:
            if isinstance(item, dict) and key:
                identifier = item.get(key)
                if identifier not in seen:
                    seen.add(identifier)
                    result.append(item)
            elif isinstance(item, (str, int, float, tuple)):
                if item not in seen:
                    seen.add(item)
                    result.append(item)
            else:
                # For unhashable types, just append
                result.append(item)
        
        return result
