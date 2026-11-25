"""Data models for the review system."""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Finding(BaseModel):
    id: str
    tool: str
    rule: Optional[str] = None
    severity: Severity
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    suggestion: Optional[str] = None
    reference: Optional[str] = None

    def to_dict(self) -> dict:
        return self.model_dump(exclude_none=True)


class ReviewResult(BaseModel):
    repo: str
    branch: str
    commit_sha: Optional[str] = None
    overall_severity: Severity
    findings: list[Finding] = []
    summary: str = ""
    confidence: float = 0.0
    metadata: dict = {}

    def to_dict(self) -> dict:
        return {
            "repo": self.repo,
            "branch": self.branch,
            "commit_sha": self.commit_sha,
            "overall_severity": self.overall_severity.value,
            "findings_count": len(self.findings),
            "findings": [f.to_dict() for f in self.findings],
            "summary": self.summary,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }

    @property
    def is_critical(self) -> bool:
        return any(f.severity == Severity.CRITICAL for f in self.findings)


class KnowledgeBaseEntry(BaseModel):
    id: str
    content: str
    tags: list[str] = []
    applicable_patterns: list[str] = []

    def to_dict(self) -> dict:
        return self.model_dump()
