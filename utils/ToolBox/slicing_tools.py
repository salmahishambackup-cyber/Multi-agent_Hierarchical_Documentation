from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SliceResult:
    text: str
    start_byte: int
    end_byte: int


def slice_file_by_bytes(file_path: Path, start_byte: int, end_byte: int) -> SliceResult:
    b = file_path.read_bytes()
    chunk = b[start_byte:end_byte]
    return SliceResult(
        text=chunk.decode("utf-8", errors="replace"),
        start_byte=start_byte,
        end_byte=end_byte,
    )