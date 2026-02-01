from pathlib import Path
from typing import Dict, Any, List, Tuple

class FileMetricsExtractor:
    """
    Extract file-level metrics for code analysis.
    Includes LOC, complexity hints, size classification.
    """
    
    # Size thresholds (LOC)
    SIZE_THRESHOLDS = {
        "small": (0, 100),
        "medium": (100, 500),
        "large": (500, 2000),
        "monolithic": (2000, float('inf'))
    }
    
    # Complexity indicators (nested depth)
    COMPLEXITY_HINTS = {
        "simple": (0, 2),           # Max nesting depth
        "moderate": (2, 4),
        "complex": (4, 6),
        "highly_complex": (6, float('inf'))
    }
    
    @staticmethod
    def count_lines(content: bytes) -> Tuple[int, int, int]:
        """
        Count lines in source code.
        
        Returns:
            (total_lines, code_lines, comment_lines)
        """
        try:
            text = content.decode('utf-8', errors='ignore')
        except:
            return 0, 0, 0
        
        lines = text.split('\n')
        total = len(lines)
        code_lines = 0
        comment_lines = 0
        
        in_multiline_comment = False
        
        for line in lines:
            stripped = line.strip()
            
            # Skip empty lines
            if not stripped:
                continue
            
            # Multiline comments (language agnostic)
            if '"""' in stripped or "'''" in stripped or '/*' in stripped or '*/' in stripped:
                in_multiline_comment = not in_multiline_comment
                comment_lines += 1
                continue
            
            if in_multiline_comment:
                comment_lines += 1
                continue
            
            # Single line comments
            if stripped.startswith('#') or stripped.startswith('//'):
                comment_lines += 1
                continue
            
            code_lines += 1
        
        return total, code_lines, comment_lines
    
    @staticmethod
    def estimate_complexity(ast_summary: dict, language: str) -> Dict[str, Any]:
        """
        Estimate code complexity from AST.
        
        Metrics:
        - Max nesting depth (estimated)
        - Function count
        - Class count
        - Average function size (if LOC known)
        """
        imports = len(ast_summary.get("imports", []))
        functions = len(ast_summary.get("functions", []))
        classes = len(ast_summary.get("classes", []))
        
        # Simple complexity heuristic: functions + classes
        complexity_score = (functions * 1.5) + (classes * 2)
        
        # Estimate nesting depth (rough heuristic)
        if classes > 0 and functions > 0:
            avg_methods_per_class = functions / classes
            estimated_depth = min(3 + (avg_methods_per_class / 5), 6)
        else:
            estimated_depth = 1 + (functions / 10)
        
        # Classify complexity
        complexity_class = "simple"
        for cls, (min_d, max_d) in FileMetricsExtractor.COMPLEXITY_HINTS.items():
            if min_d <= estimated_depth < max_d:
                complexity_class = cls
                break
        
        return {
            "estimated_nesting_depth": round(estimated_depth, 1),
            "complexity_class": complexity_class,
            "function_count": functions,
            "class_count": classes,
            "import_count": imports,
            "complexity_score": round(complexity_score, 1)
        }
    
    @staticmethod
    def classify_size(code_lines: int) -> str:
        """Classify file size by LOC."""
        for size_class, (min_loc, max_loc) in FileMetricsExtractor.SIZE_THRESHOLDS.items():
            if min_loc <= code_lines < max_loc:
                return size_class
        return "unknown"
    
    @staticmethod
    def extract_metrics(ast_summary: dict, content: bytes, language: str) -> Dict[str, Any]:
        """
        Extract all metrics for a file.
        
        Returns:
            {
                "lines_of_code": {
                    "total": int,
                    "code": int,
                    "comment": int,
                    "code_ratio": float
                },
                "size_classification": str,
                "complexity": {
                    "estimated_nesting_depth": float,
                    "complexity_class": str,
                    "function_count": int,
                    "class_count": int,
                    "import_count": int,
                    "complexity_score": float
                },
                "language": str
            }
        """
        total, code, comment = FileMetricsExtractor.count_lines(content)
        code_ratio = code / total if total > 0 else 0
        size_class = FileMetricsExtractor.classify_size(code)
        complexity = FileMetricsExtractor.estimate_complexity(ast_summary, language)
        
        return {
            "lines_of_code": {
                "total": total,
                "code": code,
                "comment": comment,
                "code_ratio": round(code_ratio, 2)
            },
            "size_classification": size_class,
            "complexity": complexity,
            "language": language
        }


def aggregate_repository_metrics(ast_summaries_with_metrics: List[Dict]) -> Dict[str, Any]:
    """
    Aggregate metrics across entire repository.
    
    Returns:
        {
            "total_files": int,
            "total_loc": int,
            "avg_loc_per_file": float,
            "language_distribution": {...},
            "size_distribution": {...},
            "complexity_distribution": {...}
        }
    """
    if not ast_summaries_with_metrics:
        return {
            "total_files": 0,
            "total_loc": 0,
            "avg_loc_per_file": 0,
            "language_distribution": {},
            "size_distribution": {},
            "complexity_distribution": {}
        }
    
    total_loc = sum(m.get("metrics", {}).get("lines_of_code", {}).get("code", 0) 
                   for m in ast_summaries_with_metrics)
    
    language_dist = {}
    size_dist = {}
    complexity_dist = {}
    
    for summary in ast_summaries_with_metrics:
        metrics = summary.get("metrics", {})
        
        # Language distribution
        lang = metrics.get("language", "unknown")
        language_dist[lang] = language_dist.get(lang, 0) + 1
        
        # Size distribution
        size_class = metrics.get("size_classification", "unknown")
        size_dist[size_class] = size_dist.get(size_class, 0) + 1
        
        # Complexity distribution
        complexity_class = metrics.get("complexity", {}).get("complexity_class", "unknown")
        complexity_dist[complexity_class] = complexity_dist.get(complexity_class, 0) + 1
    
    return {
        "total_files": len(ast_summaries_with_metrics),
        "total_loc": total_loc,
        "avg_loc_per_file": round(total_loc / len(ast_summaries_with_metrics), 1) if ast_summaries_with_metrics else 0,
        "language_distribution": language_dist,
        "size_distribution": size_dist,
        "complexity_distribution": complexity_dist
    }


def compute_file_metrics(ast_summary: dict, content: bytes, language: str) -> Dict[str, Any]:
    """
    Convenience function to compute file metrics.
    
    Args:
        ast_summary: AST summary dict
        content: File content as bytes
        language: Language of the file
        
    Returns:
        Dictionary with file metrics
    """
    return FileMetricsExtractor.extract_metrics(ast_summary, content, language)