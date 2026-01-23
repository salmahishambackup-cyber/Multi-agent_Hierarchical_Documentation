from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


DocKind = Literal["module", "function", "class"]


class ByteLocation(BaseModel):
    start_byte: int
    end_byte: int


class SymbolDoc(BaseModel):
    kind: DocKind
    module_path: str
    name: str
    signature: str
    fqname: str
    location: Optional[ByteLocation] = None
    code_hash: str
    docstring: str
    cached: bool = False
    validation_issues: List[str] = Field(default_factory=list)


class ModuleDoc(BaseModel):
    module_path: str
    module_name: str
    docstring: str
    code_hash: str
    symbols: List[SymbolDoc] = Field(default_factory=list)


class DocArtifacts(BaseModel):
    project_key: str
    repo_root: str
    model_id: str
    llm_params: Dict[str, Any]
    modules: List[ModuleDoc]


class PlanTask(BaseModel):
    task_id: str
    module_path: str
    kind: DocKind
    symbol: Optional[str] = None  # for function/class tasks
    node_id: Optional[str] = None


class DocPlan(BaseModel):
    project_key: str
    module_order: List[str]
    tasks: List[PlanTask]


class QualityReport(BaseModel):
    project_key: str
    totals: Dict[str, Any]
    issues: List[Dict[str, Any]] = Field(default_factory=list)