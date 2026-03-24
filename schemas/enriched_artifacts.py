"""
Pydantic schema definitions for enriched artifacts.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Severity levels
# ---------------------------------------------------------------------------

class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    MAJOR = "MAJOR"
    MINOR = "MINOR"


# ---------------------------------------------------------------------------
# Weakness report models
# ---------------------------------------------------------------------------

class Weakness(BaseModel):
    """A single detected weakness in an artifact."""

    artifact: str = Field(..., description="Artifact filename (e.g. doc_artifacts.json)")
    entry_id: Optional[str] = Field(None, description="Entry identifier (name, id, or index)")
    field: Optional[str] = Field(None, description="Affected field name, if applicable")
    severity: Severity = Field(..., description="Severity level: CRITICAL, MAJOR, or MINOR")
    message: str = Field(..., description="Human-readable description of the weakness")


class WeaknessReport(BaseModel):
    """Structured weakness report produced by the ArtifactCritic agent."""

    artifact_dir: str = Field(..., description="Path to the artifacts directory that was inspected")
    weaknesses: List[Weakness] = Field(default_factory=list, description="All detected weaknesses")

    # Convenience counts
    @property
    def critical_count(self) -> int:
        return sum(1 for w in self.weaknesses if w.severity == Severity.CRITICAL)

    @property
    def major_count(self) -> int:
        return sum(1 for w in self.weaknesses if w.severity == Severity.MAJOR)

    @property
    def minor_count(self) -> int:
        return sum(1 for w in self.weaknesses if w.severity == Severity.MINOR)

    def has_blocking_issues(self) -> bool:
        """Return True when CRITICAL or MAJOR weaknesses exist."""
        return self.critical_count > 0 or self.major_count > 0

    def summary(self) -> str:
        return (
            f"Weaknesses — CRITICAL: {self.critical_count}, "
            f"MAJOR: {self.major_count}, MINOR: {self.minor_count}"
        )


# ---------------------------------------------------------------------------
# Enriched documentation entry
# ---------------------------------------------------------------------------

class ParameterDoc(BaseModel):
    """Documentation for a single parameter."""

    name: str
    type: str = "Any"
    description: str = ""
    required: bool = True
    default: Optional[str] = None


class ReturnDoc(BaseModel):
    """Documentation for a return value."""

    type: str = "Any"
    description: str = ""


class RaisesDoc(BaseModel):
    """Documentation for a raised exception."""

    exception: str
    condition: str = ""


class EnrichedDocEntry(BaseModel):
    """Fully enriched documentation entry for a function, method, or class."""

    name: str = Field(..., description="Resolved name — never 'unknown'")
    file: str = Field(..., description="Source file path")
    type: str = Field(
        ...,
        description="One of: function / method / classmethod / staticmethod / property / class",
    )
    signature: str = Field("", description="Full signature with typed parameters")
    short_description: str = Field("", description="One crisp sentence summary")
    detailed_description: str = Field("", description="Full multi-sentence explanation")
    business_context: str = Field(
        "", description="Why this exists from the product / business perspective"
    )
    pipeline_stage: str = Field("", description="Which stage / layer of the system this belongs to")
    parameters: List[ParameterDoc] = Field(default_factory=list)
    returns: ReturnDoc = Field(default_factory=ReturnDoc)
    raises: List[RaisesDoc] = Field(default_factory=list)
    side_effects: List[str] = Field(
        default_factory=list,
        description="File I/O, DB writes, API calls, logging, mutations",
    )
    dependencies: List[str] = Field(
        default_factory=list, description="Internal modules + external libraries used"
    )
    example: str = Field("", description="Concrete usage snippet")


# ---------------------------------------------------------------------------
# Enriched AST entry
# ---------------------------------------------------------------------------

class EnrichedASTEntry(BaseModel):
    """AST entry enhanced with semantic metadata."""

    file: str
    language: str = ""
    semantic_role: str = Field("", description="Role of this file/symbol in the system")
    layer: str = Field("", description="Architectural layer (e.g. 'infrastructure', 'domain')")
    return_type: str = Field("", description="Inferred or declared return type")
    functions: List[Dict[str, Any]] = Field(default_factory=list)
    classes: List[Dict[str, Any]] = Field(default_factory=list)
    imports: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Enriched dependency
# ---------------------------------------------------------------------------

class EnrichedDependency(BaseModel):
    """Dependency entry enriched with purpose and version information."""

    name: str
    kind: str = Field("", description="internal / external / runtime")
    version: str = Field("", description="Version constraint or installed version")
    purpose: str = Field("", description="What this dependency is used for")


# ---------------------------------------------------------------------------
# Enriched component
# ---------------------------------------------------------------------------

class EnrichedComponent(BaseModel):
    """Component entry enriched with business and architectural metadata."""

    component_id: str = ""
    name: str
    files: List[str] = Field(default_factory=list)
    type: str = ""
    business_role: str = Field("", description="Business purpose this component fulfills")
    architectural_layer: str = Field(
        "", description="Architectural layer (e.g. 'presentation', 'service', 'data')"
    )
