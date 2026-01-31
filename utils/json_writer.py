"""JSON writing utilities with metadata support."""

import json
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime


def write_json(
    file_path: Path | str,
    data: Any,
    metadata: Optional[Dict[str, Any]] = None,
    indent: int = 2,
) -> None:
    """
    Write data to JSON file with optional metadata.
    
    Args:
        file_path: Path to output file
        data: Data to write
        metadata: Optional metadata to include
        indent: JSON indentation level
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    output = data
    if metadata:
        output = {
            "metadata": metadata,
            "data": data
        }
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=indent, ensure_ascii=False)


def write_json_with_timestamp(
    file_path: Path | str,
    data: Any,
    additional_metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Write JSON with automatic timestamp metadata.
    
    Args:
        file_path: Path to output file
        data: Data to write
        additional_metadata: Additional metadata fields
    """
    metadata = {
        "generated_at": datetime.now().isoformat(),
        "version": "1.0",
    }
    
    if additional_metadata:
        metadata.update(additional_metadata)
    
    write_json(file_path, data, metadata=metadata)
