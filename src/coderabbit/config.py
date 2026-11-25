"""Configuration management for coderabbit."""
from __future__ import annotations
from pathlib import Path
from typing import Optional
import yaml
from pydantic import BaseModel


class ReviewConfig(BaseModel):
    profile: str = "assertive"
    auto_review: bool = False
    path_filters: list[str] = []
    tone_instructions: Optional[str] = None


class ToolConfig(BaseModel):
    semgrep: bool = True
    eslint: bool = False
    pylint: bool = False
    bandit: bool = False
    custom_rules: list[str] = []


class KnowledgeBaseConfig(BaseModel):
    guidelines: Optional[str] = None
    unsafe_symbols: list[str] = []


class Config(BaseModel):
    version: int = 1
    language: Optional[str] = None
    reviews: ReviewConfig = ReviewConfig()
    tools: ToolConfig = ToolConfig()
    knowledge_base: KnowledgeBaseConfig = KnowledgeBaseConfig()

    @classmethod
    def load(cls, path: Optional[Path] = None) -> Config:
        if path is None:
            for candidate in [Path.cwd() / ".coderabbit.yaml", Path.cwd() / ".coderabbit.yml", Path.home() / ".config" / "coderabbit" / "config.yaml"]:
                if candidate.exists():
                    path = candidate
                    break
        if path and path.exists():
            with open(path) as f:
                return cls(**yaml.safe_load(f))
        return cls()

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            yaml.dump(self.model_dump(), f, default_flow_style=False)
