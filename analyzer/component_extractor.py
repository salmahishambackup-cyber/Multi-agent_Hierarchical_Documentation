from collections import defaultdict
import hashlib
from pathlib import Path

def group_by_directory(all_files: set) -> dict:
    """
    Group files by directory path.
    Returns {directory -> list of files in that directory}
    """
    dir_groups = defaultdict(list)
    
    for file in all_files:
        # Normalize to POSIX
        normalized = file.replace("\\", "/")
        directory = "/".join(normalized.split("/")[:-1]) or "root"
        dir_groups[directory].append(file)
    
    return dir_groups


def detect_naming_pattern(files: list) -> str | None:
    """
    Detect if a group of files follows a naming pattern.
    Returns the pattern name or None.
    
    Patterns:
    - "*_client.py" → "client_implementations"
    - "*_test.py" or "test_*.py" → already handled separately
    - "route.ts" in same dir → "api_routes"
    """
    if not files:
        return None
    
    # Normalize paths
    normalized = [f.replace("\\", "/").split("/")[-1].lower() for f in files]
    
    # Check for *_client pattern (Python)
    if all("_client" in n for n in normalized if n.endswith(".py")):
        return "client_implementations"
    
    # Check for api routes (TypeScript)
    if all("route.ts" in n for n in normalized):
        return "api_routes"
    
    # Check for handler pattern
    if all(("handler" in n or "controller" in n) for n in normalized):
        return "request_handlers"
    
    return None


def find_hub_and_spoke_clusters(file_imports: dict, all_files: set) -> list[set]:
    """
    Detect hub-and-spoke patterns where multiple files import a common hub.
    
    Returns list of clusters, each being a set of files (hub + spokes).
    """
    hub_clusters = []
    processed = set()
    
    # For each file that's imported by multiple others
    import_counts = defaultdict(int)
    for source, targets in file_imports.items():
        for target, edge_kind in targets:
            import_counts[target] += 1
    
    # Find hubs (files imported by 2+ files)
    hubs = {target for target, count in import_counts.items() if count >= 2}
    
    for hub in hubs:
        if hub in processed:
            continue
        
        # Find all files that import this hub
        spokes = set()
        for source, targets in file_imports.items():
            for target, edge_kind in targets:
                if target == hub:
                    spokes.add(source)
        
        if len(spokes) >= 2:  # Only form cluster if 2+ spokes
            cluster = spokes | {hub}
            hub_clusters.append(cluster)
            processed.update(cluster)
    
    return hub_clusters


def merge_nearby_clusters(clusters: list[set], max_distance: float = 0.3) -> list[set]:
    """
    Merge clusters that are "nearby" in the import graph.
    
    If two clusters share multiple files or have tight coupling,
    merge them into one.
    """
    merged = list(clusters)
    changed = True
    
    while changed:
        changed = False
        new_merged = []
        used = set()
        
        for i, cluster1 in enumerate(merged):
            if i in used:
                continue
            
            combined = cluster1.copy()
            for j, cluster2 in enumerate(merged[i+1:], start=i+1):
                if j in used:
                    continue
                
                # Check overlap and coupling
                overlap = len(cluster1 & cluster2)
                union = len(cluster1 | cluster2)
                jaccard = overlap / union if union > 0 else 0
                
                # Merge if Jaccard similarity > threshold
                if jaccard > max_distance:
                    combined |= cluster2
                    used.add(j)
                    changed = True
            
            new_merged.append(combined)
        
        merged = new_merged
    
    return merged


def enrich_components_with_heuristics(components: list[dict], 
                                      ast_summaries: list[dict],
                                      file_imports: dict,
                                      all_files: set) -> list[dict]:
    """
    Enhance components by merging clusters found through heuristics.
    
    Detects:
    1. Directory-based groupings
    2. Naming pattern clusters
    3. Hub-and-spoke patterns
    """
    
    # Get current component files (grouped)
    current_clusters = [set(comp["files"]) for comp in components]
    processed_files = set().union(*current_clusters)
    
    # Find unprocessed files
    unprocessed = all_files - processed_files
    
    if not unprocessed:
        return components
    
    # Apply heuristics to unprocessed files
    extra_clusters = []
    
    # 1. Group by directory
    dir_groups = group_by_directory(unprocessed)
    for directory, files in dir_groups.items():
        if len(files) >= 2:  # Only cluster if 2+ files
            extra_clusters.append(set(files))
    
    # 2. Detect hub-and-spoke patterns
    hub_clusters = find_hub_and_spoke_clusters(file_imports, unprocessed)
    extra_clusters.extend(hub_clusters)
    
    # 3. Merge overlapping clusters
    merged_clusters = merge_nearby_clusters(extra_clusters)
    
    # Convert to components
    file_language_map = {entry["file"]: entry.get("language", "unknown") 
                         for entry in ast_summaries}
    
    for cluster_files in merged_clusters:
        cluster_files = sorted(cluster_files)
        
        # Get languages
        cluster_langs = {file_language_map.get(f, "unknown") for f in cluster_files}
        
        # Calculate cohesion
        cohesion = calculate_cohesion(cluster_files, file_imports, {})
        
        # Determine hypothesis
        naming_pattern = detect_naming_pattern(cluster_files)
        if naming_pattern:
            hypothesis = f"Pattern-based cluster ({naming_pattern}): {len(cluster_files)} files"
        else:
            hypothesis = f"Directory-based cluster: {len(cluster_files)} files"
        
        components.append({
            "component_id": generate_component_id(",".join(cluster_files)),
            "hypothesis": hypothesis,
            "files": cluster_files,
            "languages": sorted(cluster_langs),
            "evidence": [
                f"Grouped by heuristic (directory/pattern/hub-spoke)",
                f"Internal dependencies: {cohesion['internal_edges']}",
                f"Cohesion density: {cohesion['density']}"
            ],
            "cohesion": cohesion,
            "confidence": cohesion["confidence"] * 0.85  # Reduce confidence for heuristic-based
        })
    
    return components


def generate_component_id(name: str) -> str:
    """Generate deterministic component ID from name."""
    return "C_" + hashlib.md5(name.encode()).hexdigest()[:8]


def build_file_graph(dependency_graph: dict, include_cross_language: bool = True) -> dict:
    """
    Build file-to-file import graph from dependency edges.
    
    Can include cross-language edges to form language-agnostic components
    or exclude them for language-specific clustering.
    
    Returns:
        {file -> set of (target_file, edge_kind) tuples}
    """
    file_imports = defaultdict(set)
    
    for edge in dependency_graph.get("edges", []):
        # Include internal modules (always)
        # Include cross-language (if requested)
        # Exclude uncertain_dynamic and external (not structural)
        if edge["kind"] not in ("internal_module", "cross_language"):
            continue
        
        if edge["kind"] == "cross_language" and not include_cross_language:
            continue
        
        source = edge["from"]
        target = edge["to"].replace("internal:", "")
        edge_kind = edge["kind"]
        
        # Store both target and edge kind for later analysis
        file_imports[source].add((target, edge_kind))
    
    return file_imports


def validate_graph_connectivity(file_imports: dict, all_files: set) -> dict:
    """
    Validate graph connectivity and report metrics.
    
    Returns:
        {
            "total_files": int,
            "files_with_edges": int,
            "total_edge_count": int,
            "orphan_files": int,
            "avg_edges_per_file": float,
            "max_edges": int,
            "warnings": [str]
        }
    """
    warnings = []
    edge_count = sum(len(targets) for targets in file_imports.values())
    files_with_edges = len([f for f, targets in file_imports.items() if targets])
    orphan_files = len(all_files) - files_with_edges
    
    # Check for path mismatches
    files_in_graph = set(file_imports.keys())
    missing_from_graph = all_files - files_in_graph
    
    if missing_from_graph:
        warnings.append(
            f"⚠️  {len(missing_from_graph)} files have no outgoing edges: "
            f"{list(missing_from_graph)[:3]}..."  # Show first 3
        )
    
    # Check for edge targets outside known files
    all_targets = set()
    for targets in file_imports.values():
        # Extract file paths from (target_file, edge_kind) tuples
        for target, edge_kind in targets:
            all_targets.add(target)
    
    unknown_targets = all_targets - all_files
    if unknown_targets:
        warnings.append(
            f"⚠️  {len(unknown_targets)} edge targets are not in AST: "
            f"{list(unknown_targets)[:3]}..."
        )
    
    avg_edges = edge_count / len(file_imports) if file_imports else 0
    max_edges = max(len(targets) for targets in file_imports.values()) if file_imports else 0
    
    return {
        "total_files": len(all_files),
        "files_with_edges": files_with_edges,
        "total_edge_count": edge_count,
        "orphan_files": orphan_files,
        "avg_edges_per_file": round(avg_edges, 2),
        "max_edges": max_edges,
        "warnings": warnings
    }


def find_connected_component(start_file: str, 
                             file_imports: dict,
                             visited: set) -> set:
    """
    Find all files connected to start_file through mutual dependencies.
    Works with new (target, edge_kind) tuple format.
    Uses BFS to explore bidirectional imports.
    """
    if start_file in visited:
        return set()
    
    stack = [start_file]
    component = set()
    
    while stack:
        current = stack.pop()
        if current in visited:
            continue
        
        visited.add(current)
        component.add(current)
        
        # Forward edges: files that current imports
        for target, edge_kind in file_imports.get(current, set()):
            if target not in visited:
                stack.append(target)
        
        # Reverse edges: files that import current
        for source, targets in file_imports.items():
            for target, edge_kind in targets:
                if target == current and source not in visited:
                    stack.append(source)
    
    return component

def calculate_cohesion(files: list[str], 
                       file_imports: dict,
                       dependency_graph: dict) -> dict:
    """
    Calculate cohesion metrics for a component.
    Counts edges by kind for detailed analysis.
    
    Returns:
        {
            "internal_edges": count,
            "cross_language_edges": count,
            "external_edges": count,
            "density": float,
            "confidence": float in [0, 1],
            "edge_breakdown": {...}
        }
    """
    file_set = set(files)
    internal_edges = 0
    cross_language_edges = 0
    external_edges = 0
    
    for file in files:
        for target, edge_kind in file_imports.get(file, set()):
            if target in file_set:
                if edge_kind == "cross_language":
                    cross_language_edges += 1
                else:
                    internal_edges += 1
            else:
                external_edges += 1
    
    # Calculate density
    total_internal_connections = internal_edges + cross_language_edges
    max_possible = len(files) * (len(files) - 1)
    density = total_internal_connections / max_possible if max_possible > 0 else 0
    
    # Confidence based on cohesion
    if len(files) == 1:
        confidence = 0.3
    else:
        total_edges = internal_edges + cross_language_edges + external_edges
        if total_edges == 0:
            confidence = 0.4
        else:
            internal_ratio = total_internal_connections / total_edges
            # Map: 0.0 → 0.4, 0.5 → 0.6, 1.0 → 0.9
            confidence = 0.4 + (internal_ratio * 0.5)
    
    return {
        "internal_edges": internal_edges,
        "cross_language_edges": cross_language_edges,
        "external_edges": external_edges,
        "density": round(density, 3),
        "confidence": round(min(confidence, 0.95), 2),
        "edge_breakdown": {
            "same_language": internal_edges,
            "cross_language": cross_language_edges,
            "external": external_edges
        }
    }

def is_test_file(file_path: str) -> bool:
    """Identify test files by name patterns."""
    normalized = file_path.lower().replace("\\", "/")
    test_patterns = {"test_", "_test.", "tests/", "test/", "__tests__"}
    return any(pattern in normalized for pattern in test_patterns)


def extract_components(ast_summaries: list[dict],
                       dependency_graph: dict) -> list[dict]:
    """
    Extract semantic components using graph-based clustering with validation.
    
    Includes diagnostics to catch connectivity issues.
    """
    
    if not ast_summaries or not dependency_graph.get("edges"):
        # Empty repo or no dependencies
        components = []
        for entry in ast_summaries:
            components.append({
                "component_id": generate_component_id(entry["file"]),
                "hypothesis": "Singleton (no dependencies)",
                "files": [entry["file"]],
                "evidence": ["No internal module imports"],
                "cohesion": {"internal_edges": 0, "external_edges": 0, "density": 0, "confidence": 0.3},
                "confidence": 0.3
            })
        return components
    
    # Build dependency structures
    # Include cross-language edges for richer clustering
    file_imports = build_file_graph(dependency_graph, include_cross_language=True)
    all_files = {entry["file"] for entry in ast_summaries}
    
    # ========== VALIDATION & DIAGNOSTICS ==========
    connectivity_report = validate_graph_connectivity(file_imports, all_files)
    
    # Add diagnostics to a metadata field (can be logged or reported separately)
    # These warnings indicate issues that should be investigated
    if connectivity_report["warnings"]:
        print(f"\n[COMPONENT EXTRACTION DIAGNOSTICS]")
        print(f"Total files: {connectivity_report['total_files']}")
        print(f"Files with edges: {connectivity_report['files_with_edges']}")
        print(f"Total edges: {connectivity_report['total_edge_count']}")
        print(f"Avg edges/file: {connectivity_report['avg_edges_per_file']}")
        for warning in connectivity_report["warnings"]:
            print(warning)
    
    # Find connected components
    visited = set()
    raw_components = []
    
    for file in all_files:
        if file not in visited:
            component = find_connected_component(file, file_imports, visited)
            if component:
                raw_components.append(component)
    
    # Post-process: refine and separate test files
    components = []
    processed_files = set()
    
    for component_files in raw_components:
        if any(f in processed_files for f in component_files):
            continue
        
        component_files = sorted(component_files)
        processed_files.update(component_files)
        
        # Separate test files
        test_files = [f for f in component_files if is_test_file(f)]
        prod_files = [f for f in component_files if not is_test_file(f)]
        
        # Create production component
        if prod_files:
            cohesion = calculate_cohesion(prod_files, file_imports, dependency_graph)
            
            # Get languages in this component
            file_langs = {}
            for entry in ast_summaries:
                if entry["file"] in prod_files:
                    file_langs[entry["file"]] = entry.get("language", "unknown")
            
            unique_languages = set(file_langs.values())
            
            components.append({
                "component_id": generate_component_id(",".join(prod_files)),
                "hypothesis": f"Semantic component: {len(prod_files)} interconnected files ({', '.join(unique_languages)})",
                "files": prod_files,
                "languages": sorted(unique_languages),
                "evidence": [
                    f"Internal dependencies: {cohesion['internal_edges']}",
                    f"Cross-language dependencies: {cohesion['cross_language_edges']}",
                    f"External dependencies: {cohesion['external_edges']}",
                    f"Cohesion density: {cohesion['density']}"
                ],
                "cohesion": cohesion,
                "confidence": cohesion["confidence"]
            })
        
        # Create test component (if tests exist)
        if test_files:
            test_cohesion = calculate_cohesion(test_files, file_imports, dependency_graph)
            
            components.append({
                "component_id": generate_component_id("tests_" + ",".join(test_files)),
                "hypothesis": f"Test suite: {len(test_files)} test files",
                "files": test_files,
                "evidence": [
                    f"Test files for related functionality",
                    f"Internal test dependencies: {test_cohesion['internal_edges']}"
                ],
                "cohesion": test_cohesion,
                "confidence": 0.5  # Test components have inherent lower confidence
            })
    
    # Ensure all files are covered
    for entry in ast_summaries:
        file = entry["file"]
        if file not in processed_files:
            components.append({
                "component_id": generate_component_id(file),
                "hypothesis": "Isolated file (no internal dependencies)",
                "files": [file],
                "evidence": ["Unreachable through internal module graph"],
                "cohesion": {"internal_edges": 0, "external_edges": 0, "density": 0, "confidence": 0.2},
                "confidence": 0.2
            })
            processed_files.add(file)
    
    # ========== HEURISTIC ENRICHMENT ==========
    # Enhance components by detecting directory-based and pattern-based groupings
    components = enrich_components_with_heuristics(
        components, 
        ast_summaries, 
        file_imports, 
        all_files
    )
    
    return components