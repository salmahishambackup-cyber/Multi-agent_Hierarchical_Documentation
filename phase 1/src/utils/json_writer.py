# src/utils/json_writer.py
import json
from pathlib import Path
from typing import Any, List, Union
from datetime import datetime


class SafeJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder that safely handles non-serializable types.
    Converts them to string representations for serialization.
    """
    def default(self, obj):
        # Handle sets
        if isinstance(obj, set):
            return list(obj)
        # Handle tuples
        elif isinstance(obj, tuple):
            return list(obj)
        # Handle paths
        elif isinstance(obj, Path):
            return str(obj)
        # Handle other types by converting to string
        else:
            return str(obj)


def sanitize_evidence(evidence: Any) -> Any:
    """
    Recursively convert evidence to JSON-serializable format.
    
    Handles:
    - Sets → lists
    - Tuples → lists
    - Non-serializable objects → strings
    """
    if isinstance(evidence, dict):
        return {k: sanitize_evidence(v) for k, v in evidence.items()}
    elif isinstance(evidence, list):
        return [sanitize_evidence(item) for item in evidence]
    elif isinstance(evidence, set):
        return list(evidence)
    elif isinstance(evidence, tuple):
        return list(evidence)
    elif isinstance(evidence, (str, int, float, bool, type(None))):
        return evidence
    else:
        # Convert unknown types to string
        return str(evidence)


def sanitize_payload(data: Any) -> Any:
    """
    Recursively sanitize entire payload for JSON serialization.
    
    Walks through nested structures and converts non-serializable types.
    """
    if isinstance(data, dict):
        return {k: sanitize_payload(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_payload(item) for item in data]
    elif isinstance(data, set):
        return list(data)
    elif isinstance(data, tuple):
        return list(data)
    elif isinstance(data, (str, int, float, bool, type(None))):
        return data
    else:
        return str(data)


def validate_edges_serializable(edges: list) -> bool:
    """
    Validate that all edges and their evidence are JSON-serializable.
    
    Returns True if valid, raises exception otherwise.
    """
    for i, edge in enumerate(edges):
        try:
            json.dumps(edge, cls=SafeJSONEncoder)
        except (TypeError, ValueError) as e:
            raise ValueError(
                f"Edge {i} contains non-serializable data: {edge}\nError: {e}"
            )
    return True


def write_json(path: str, data: dict, metadata: dict | None = None) -> None:
    """
    Write a JSON artifact with metadata and timestamp.
    
    Validates and sanitizes all data before serialization.
    Logs warnings if non-standard types are encountered.
    
    Args:
        path: Output file path
        data: Data to serialize (list or dict)
        metadata: Optional metadata dict to include
    """
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "metadata": metadata or {},
        "timestamp": datetime.utcnow().isoformat(),
        "data": data
    }

    # Sanitize payload to ensure JSON serializability
    payload = sanitize_payload(payload)

    # Validate edges if data contains them
    if isinstance(data, dict) and "edges" in data:
        try:
            validate_edges_serializable(data["edges"])
        except ValueError as e:
            # Log warning but continue (with sanitized version)
            import sys
            print(f"[WARNING] {path}: {e}", file=sys.stderr)

    # Write with custom encoder and UTF-8 encoding
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                payload,
                f,
                indent=2,
                cls=SafeJSONEncoder,
                ensure_ascii=False
            )
    except (TypeError, ValueError) as e:
        raise RuntimeError(
            f"Failed to serialize {path}: {e}\n"
            f"Payload structure: {type(payload)}, Data type: {type(data)}"
        )