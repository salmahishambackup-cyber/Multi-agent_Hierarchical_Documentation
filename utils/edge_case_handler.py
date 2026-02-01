"""Edge case detection utilities."""

from typing import Dict, List, Set, Any
from dataclasses import dataclass, field
from pathlib import Path
import re


@dataclass
class CircularImportInfo:
    """Information about a circular import."""
    cycle: List[str]
    severity: str = "warning"  # warning, error


@dataclass
class MonolithicFileInfo:
    """Information about a monolithic file."""
    file: str
    lines_of_code: int
    num_functions: int
    num_classes: int
    severity: str = "warning"


@dataclass
class GeneratedCodeInfo:
    """Information about generated code."""
    file: str
    indicators: List[str]
    confidence: str = "medium"  # low, medium, high


@dataclass
class EdgeCaseReport:
    """Aggregated edge case findings."""
    circular_imports: List[CircularImportInfo] = field(default_factory=list)
    monolithic_files: List[MonolithicFileInfo] = field(default_factory=list)
    generated_files: List[GeneratedCodeInfo] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "circular_imports": [
                {"cycle": ci.cycle, "severity": ci.severity}
                for ci in self.circular_imports
            ],
            "monolithic_files": [
                {
                    "file": mf.file,
                    "lines_of_code": mf.lines_of_code,
                    "num_functions": mf.num_functions,
                    "num_classes": mf.num_classes,
                    "severity": mf.severity
                }
                for mf in self.monolithic_files
            ],
            "generated_files": [
                {
                    "file": gf.file,
                    "indicators": gf.indicators,
                    "confidence": gf.confidence
                }
                for gf in self.generated_files
            ]
        }
    
    def has_issues(self) -> bool:
        """Check if there are any edge cases."""
        return bool(
            self.circular_imports or 
            self.monolithic_files or 
            self.generated_files
        )


class CircularImportDetector:
    """Detects circular import dependencies."""
    
    @staticmethod
    def detect(dependency_graph: Dict[str, Any]) -> List[CircularImportInfo]:
        """
        Detect circular imports in dependency graph.
        
        Args:
            dependency_graph: Graph with nodes and edges
            
        Returns:
            List of circular import information
        """
        cycles = []
        edges = dependency_graph.get("edges", [])
        
        # Build adjacency list
        graph: Dict[str, List[str]] = {}
        for edge in edges:
            from_node = edge.get("from", "")
            to_node = edge.get("to", "")
            if from_node and to_node:
                if from_node not in graph:
                    graph[from_node] = []
                graph[from_node].append(to_node)
        
        # DFS to find cycles
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        path: List[str] = []
        
        def dfs(node: str) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(CircularImportInfo(cycle=cycle))
            
            path.pop()
            rec_stack.remove(node)
        
        for node in graph:
            if node not in visited:
                dfs(node)
        
        return cycles


class MonolithicFileDetector:
    """Detects overly large monolithic files."""
    
    # Thresholds
    LOC_THRESHOLD = 1000  # Lines of code
    FUNCTION_THRESHOLD = 50  # Number of functions
    CLASS_THRESHOLD = 20  # Number of classes
    
    @staticmethod
    def detect(ast_data: Dict[str, Any], file_metrics: Dict[str, Any] = None) -> List[MonolithicFileInfo]:
        """
        Detect monolithic files.
        
        Args:
            ast_data: AST information per file
            file_metrics: Optional file metrics data
            
        Returns:
            List of monolithic file information
        """
        monolithic = []
        
        for file_path, ast_info in ast_data.items():
            num_functions = len(ast_info.get("functions", []))
            num_classes = len(ast_info.get("classes", []))
            
            # Get LOC from metrics or estimate
            loc = 0
            if file_metrics and file_path in file_metrics:
                loc = file_metrics[file_path].get("lines_of_code", 0)
            else:
                # Rough estimate based on functions and classes
                loc = num_functions * 20 + num_classes * 50
            
            # Check thresholds
            if (loc >= MonolithicFileDetector.LOC_THRESHOLD or
                num_functions >= MonolithicFileDetector.FUNCTION_THRESHOLD or
                num_classes >= MonolithicFileDetector.CLASS_THRESHOLD):
                
                severity = "warning"
                if loc >= MonolithicFileDetector.LOC_THRESHOLD * 2:
                    severity = "error"
                
                monolithic.append(MonolithicFileInfo(
                    file=file_path,
                    lines_of_code=loc,
                    num_functions=num_functions,
                    num_classes=num_classes,
                    severity=severity
                ))
        
        return monolithic


class GeneratedCodeDetector:
    """Detects auto-generated code files."""
    
    # Common indicators of generated code
    GENERATED_PATTERNS = [
        r"(?i)auto-?generated",
        r"(?i)do not edit",
        r"(?i)generated by",
        r"(?i)code generator",
        r"@generated",
        r"<auto-generated>",
        r"This file is automatically generated",
    ]
    
    GENERATED_FILE_PATTERNS = [
        r".*_pb2\.py$",  # Protocol buffer generated files
        r".*\.generated\.",  # .generated.* files
        r".*\.g\..*",  # .g.* files (ANTLR, etc.)
    ]
    
    @staticmethod
    def detect(file_path: str, content: bytes = None) -> GeneratedCodeInfo:
        """
        Detect if a file is auto-generated.
        
        Args:
            file_path: Path to the file
            content: Optional file content
            
        Returns:
            GeneratedCodeInfo if detected, None otherwise
        """
        indicators = []
        
        # Check file name patterns
        for pattern in GeneratedCodeDetector.GENERATED_FILE_PATTERNS:
            if re.match(pattern, file_path):
                indicators.append(f"Filename matches pattern: {pattern}")
        
        # Check content if available
        if content:
            try:
                text = content.decode('utf-8', errors='ignore')
                # Check first 1000 characters
                header = text[:1000]
                
                for pattern in GeneratedCodeDetector.GENERATED_PATTERNS:
                    if re.search(pattern, header):
                        indicators.append(f"Header contains: {pattern}")
            except Exception:
                pass
        
        if indicators:
            confidence = "high" if len(indicators) >= 2 else "medium"
            return GeneratedCodeInfo(
                file=file_path,
                indicators=indicators,
                confidence=confidence
            )
        
        return None


def analyze_edge_cases(
    ast_data: Dict[str, Any],
    dependency_graph: Dict[str, Any],
    file_metrics: Dict[str, Any] = None,
    file_contents: Dict[str, bytes] = None
) -> EdgeCaseReport:
    """
    Analyze repository for edge cases.
    
    Args:
        ast_data: AST information per file
        dependency_graph: Dependency graph
        file_metrics: Optional file metrics
        file_contents: Optional file contents for generated code detection
        
    Returns:
        EdgeCaseReport with findings
    """
    report = EdgeCaseReport()
    
    # Detect circular imports
    report.circular_imports = CircularImportDetector.detect(dependency_graph)
    
    # Detect monolithic files
    report.monolithic_files = MonolithicFileDetector.detect(ast_data, file_metrics)
    
    # Detect generated code
    if file_contents:
        for file_path, content in file_contents.items():
            generated_info = GeneratedCodeDetector.detect(file_path, content)
            if generated_info:
                report.generated_files.append(generated_info)
    else:
        # Check just file names
        for file_path in ast_data.keys():
            generated_info = GeneratedCodeDetector.detect(file_path)
            if generated_info:
                report.generated_files.append(generated_info)
    
    return report
