"""
Edge Case Handler for Structural Analysis
Detects and reports special code characteristics that need special handling:
- Circular imports (dependency cycles)
- Monolithic files (>2000 LOC)
- Generated/auto-generated code (copyright headers, auto-generated markers)
"""

import json
import re
from typing import Dict, List, Set, Any
from collections import defaultdict, deque


class CircularImportDetector:
    """Detects circular dependencies in the dependency graph."""
    
    @staticmethod
    def find_cycles(dependency_graph: Dict[str, Any]) -> List[List[str]]:
        """
        Find all circular dependency cycles using DFS.
        
        Args:
            dependency_graph: Graph with 'nodes' and 'edges' structure
                             nodes: list of strings (file paths)
                             edges: list of dicts with 'from', 'to', 'kind', 'evidence'
            
        Returns:
            List of cycles, where each cycle is a list of node names
        """
        cycles = []
        
        # Build adjacency list from edges
        adj_list = defaultdict(list)
        
        for edge in dependency_graph.get('edges', []):
            src = edge['from']
            dst = edge['to']
            # Only internal file dependencies for cycle detection
            if not dst.startswith('external:'):
                adj_list[src].append(dst)
        
        # Get all nodes
        nodes = set(dependency_graph.get('nodes', []))
        
        # DFS to detect cycles
        visited = set()
        rec_stack = set()
        
        def dfs(node: str, path: List[str]) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in adj_list[node]:
                if neighbor not in visited:
                    dfs(neighbor, path[:])
                elif neighbor in rec_stack:
                    # Found cycle: from neighbor to node
                    cycle_start = path.index(neighbor) if neighbor in path else -1
                    if cycle_start >= 0:
                        cycle = path[cycle_start:] + [neighbor]
                        cycles.append(cycle)
            
            rec_stack.remove(node)
        
        for node in nodes:
            if node not in visited:
                dfs(node, [])
        
        # Deduplicate cycles
        unique_cycles = []
        seen = set()
        for cycle in cycles:
            normalized = tuple(sorted(cycle[:-1]))  # Exclude repeated last element
            if normalized not in seen:
                seen.add(normalized)
                unique_cycles.append(cycle[:-1])  # Remove duplicate end node
        
        return unique_cycles
    
    @staticmethod
    def generate_cycle_report(cycles: List[List[str]], dependency_graph: Dict) -> Dict[str, Any]:
        """Generate human-readable cycle report."""
        if not cycles:
            return {
                "total_cycles": 0,
                "cycles": [],
                "status": "✓ No circular dependencies detected"
            }
        
        cycle_reports = []
        for cycle in cycles:
            cycle_reports.append({
                "length": len(cycle),
                "path": " -> ".join(cycle) + " -> " + cycle[0]
            })
        
        return {
            "total_cycles": len(cycles),
            "cycles": cycle_reports,
            "status": f"⚠ {len(cycles)} circular dependency cycle(s) detected"
        }


class MonolithicFileDetector:
    """Identifies monolithic files that may need refactoring."""
    
    # Thresholds for different languages
    MONOLITHIC_THRESHOLDS = {
        "python": 2000,
        "typescript": 1500,
        "javascript": 1500,
        "java": 2500,
        "c": 2000,
        "cpp": 2000,
        "csharp": 2000,
    }
    
    @staticmethod
    def identify_monolithic_files(ast_summaries: List[Dict]) -> List[Dict[str, Any]]:
        """
        Identify files that exceed monolithic thresholds.
        
        Args:
            ast_summaries: List of AST summaries with metrics
            
        Returns:
            List of monolithic file reports
        """
        monolithic_files = []
        
        for file_summary in ast_summaries:
            if 'metrics' not in file_summary:
                continue
            
            metrics = file_summary['metrics']
            language = file_summary.get('language', 'unknown').lower()
            loc = metrics.get('loc', {}).get('total', 0)
            
            # Get threshold for language (default 2000)
            threshold = MonolithicFileDetector.MONOLITHIC_THRESHOLDS.get(language, 2000)
            
            if loc > threshold:
                monolithic_files.append({
                    "file_id": file_summary['file_id'],
                    "file_path": file_summary['file_path'],
                    "language": language,
                    "loc": loc,
                    "threshold": threshold,
                    "ratio": round(loc / threshold, 2),
                    "complexity": metrics.get('complexity_score', 0),
                    "functions": metrics.get('functions_count', 0),
                    "classes": metrics.get('classes_count', 0),
                    "risk_level": MonolithicFileDetector._assess_risk(loc, threshold)
                })
        
        # Sort by LOC descending
        monolithic_files.sort(key=lambda x: x['loc'], reverse=True)
        return monolithic_files
    
    @staticmethod
    def _assess_risk(loc: int, threshold: int) -> str:
        """Assess risk level based on LOC ratio."""
        ratio = loc / threshold
        if ratio < 1.5:
            return "low"
        elif ratio < 2.5:
            return "medium"
        elif ratio < 4:
            return "high"
        else:
            return "critical"
    
    @staticmethod
    def generate_monolithic_report(monolithic_files: List[Dict]) -> Dict[str, Any]:
        """Generate human-readable monolithic files report."""
        if not monolithic_files:
            return {
                "total_monolithic": 0,
                "files": [],
                "status": "✓ No monolithic files detected"
            }
        
        # Group by risk level
        by_risk = defaultdict(list)
        for file_info in monolithic_files:
            by_risk[file_info['risk_level']].append(file_info)
        
        return {
            "total_monolithic": len(monolithic_files),
            "by_risk": {
                "critical": len(by_risk.get("critical", [])),
                "high": len(by_risk.get("high", [])),
                "medium": len(by_risk.get("medium", [])),
                "low": len(by_risk.get("low", []))
            },
            "top_files": [
                {
                    "path": f['file_path'],
                    "loc": f['loc'],
                    "risk": f['risk_level']
                } for f in monolithic_files[:5]
            ],
            "status": f"⚠ {len(monolithic_files)} monolithic file(s) detected"
        }


class GeneratedCodeDetector:
    """Detects automatically generated or synthetic code."""
    
    # Markers indicating generated code
    GENERATED_MARKERS = [
        r"^[/*\s]*AUTO.{0,10}GENERATED",  # Auto-generated
        r"^[/*\s]*DO NOT (EDIT|MODIFY)",   # Don't edit warnings
        r"^[/*\s]*This file was automatically created",
        r"^[/*\s]*Generated (by|from|on)",
        r"^[/*\s]*\$\$GENERATED",
        r"^# Generated",
        r"^// Generated",
        r"@generated",  # Common in proto files
        r"autogenerated by",
    ]
    
    # Common generated file patterns
    GENERATED_FILE_PATTERNS = [
        r"\.pb\.py$",          # Protobuf
        r"\.pb\.ts$",
        r"\.pb\.js$",
        r"_pb\.py$",
        r"_pb2\.py$",
        r"\.g\.ts$",
        r"\.generated\.",
        r"(mock|stub|test).*\.py$",
        r"(venv|\.venv|node_modules)",
    ]
    
    @staticmethod
    def is_generated_code(file_path: str, file_content: str = None) -> Dict[str, Any]:
        """
        Detect if a file is generated code.
        
        Args:
            file_path: Path to the file
            file_content: Optional file content for marker detection
            
        Returns:
            Detection result with indicators
        """
        result = {
            "is_generated": False,
            "indicators": [],
            "confidence": 0.0
        }
        
        # Check file name patterns
        for pattern in GeneratedCodeDetector.GENERATED_FILE_PATTERNS:
            if re.search(pattern, file_path, re.IGNORECASE):
                result["indicators"].append(f"file_pattern: {pattern}")
                result["confidence"] += 0.3
        
        # Check file content for generated markers
        if file_content:
            lines = file_content.split('\n')[:20]  # Check first 20 lines
            content_head = '\n'.join(lines)
            
            for marker in GeneratedCodeDetector.GENERATED_MARKERS:
                if re.search(marker, content_head, re.IGNORECASE | re.MULTILINE):
                    result["indicators"].append(f"marker: {marker}")
                    result["confidence"] += 0.5
        
        result["is_generated"] = result["confidence"] >= 0.5
        return result
    
    @staticmethod
    def detect_in_batch(ast_summaries: List[Dict]) -> List[Dict[str, Any]]:
        """
        Batch-detect generated code in all files.
        
        Args:
            ast_summaries: List of AST summaries
            
        Returns:
            List of files likely to be generated
        """
        generated_files = []
        
        for summary in ast_summaries:
            file_path = summary.get('file_path', '')
            
            # Use file path for detection (content not always available)
            detection = GeneratedCodeDetector.is_generated_code(file_path)
            
            if detection['is_generated']:
                generated_files.append({
                    "file_id": summary.get('file_id'),
                    "file_path": file_path,
                    "indicators": detection['indicators'],
                    "confidence": detection['confidence']
                })
        
        return generated_files
    
    @staticmethod
    def generate_generated_code_report(generated_files: List[Dict]) -> Dict[str, Any]:
        """Generate human-readable generated code report."""
        if not generated_files:
            return {
                "total_generated": 0,
                "files": [],
                "status": "✓ No generated code detected"
            }
        
        # Sort by confidence descending
        generated_files.sort(key=lambda x: x['confidence'], reverse=True)
        
        return {
            "total_generated": len(generated_files),
            "high_confidence": len([f for f in generated_files if f['confidence'] >= 0.8]),
            "medium_confidence": len([f for f in generated_files if 0.5 <= f['confidence'] < 0.8]),
            "files": [
                {
                    "path": f['file_path'],
                    "confidence": f['confidence'],
                    "indicators": f['indicators'][:2]  # Top 2 indicators
                } for f in generated_files[:10]
            ],
            "status": f"⚠ {len(generated_files)} potentially generated file(s) detected"
        }


class EdgeCaseReport:
    """Combined edge case analysis report."""
    
    def __init__(self):
        self.circular_imports = []
        self.monolithic_files = []
        self.generated_files = []
        self.summary = {}
    
    def add_circular_imports(self, cycles: List[List[str]], graph: Dict) -> None:
        """Add circular import analysis."""
        self.circular_imports = CircularImportDetector.generate_cycle_report(cycles, graph)
    
    def add_monolithic_files(self, files: List[Dict]) -> None:
        """Add monolithic files analysis."""
        self.monolithic_files = MonolithicFileDetector.generate_monolithic_report(files)
    
    def add_generated_files(self, files: List[Dict]) -> None:
        """Add generated code analysis."""
        self.generated_files = GeneratedCodeDetector.generate_generated_code_report(files)
    
    def compute_summary(self) -> None:
        """Compute overall summary."""
        issues = []
        if self.circular_imports['total_cycles'] > 0:
            issues.append(f"{self.circular_imports['total_cycles']} cycle(s)")
        if self.monolithic_files['total_monolithic'] > 0:
            issues.append(f"{self.monolithic_files['total_monolithic']} monolithic file(s)")
        if self.generated_files['total_generated'] > 0:
            issues.append(f"{self.generated_files['total_generated']} generated file(s)")
        
        self.summary = {
            "edge_cases_detected": len(issues) > 0,
            "total_issues": sum([
                self.circular_imports['total_cycles'],
                self.monolithic_files['total_monolithic'],
                self.generated_files['total_generated']
            ]),
            "issue_breakdown": issues if issues else ["No edge cases detected"]
        }
    
    def print_summary(self) -> None:
        """Print summary to console."""
        print(f"\n[EDGE CASE DETECTION]")
        print(f"Circular imports: {self.circular_imports['total_cycles']}")
        print(f"Monolithic files: {self.monolithic_files['total_monolithic']}")
        print(f"Generated files: {self.generated_files['total_generated']}")
        
        if self.circular_imports['total_cycles'] > 0:
            for cycle_info in self.circular_imports['cycles'][:3]:
                print(f"  Cycle: {cycle_info['path']}")
        
        if self.monolithic_files['total_monolithic'] > 0:
            for file_info in self.monolithic_files['top_files'][:2]:
                print(f"  Monolithic ({file_info['risk']}): {file_info['path']} ({file_info['loc']} LOC)")
        
        if self.generated_files['total_generated'] > 0:
            for file_info in self.generated_files['files'][:2]:
                print(f"  Generated: {file_info['path']} ({file_info['confidence']:.0%})")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "edge_case_analysis": {
                "circular_imports": self.circular_imports,
                "monolithic_files": self.monolithic_files,
                "generated_files": self.generated_files,
                "summary": self.summary
            }
        }
