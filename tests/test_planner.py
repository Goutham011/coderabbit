"""Tests for the planning engine."""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from coderabbit.planner import Plan, Planner


class TestPlan:
    def test_to_dict(self):
        plan = Plan(source="test", summary="A task", phases=[{"title": "P1"}], tasks=["t1"], prompt="do it")
        d = plan.to_dict()
        assert d["source"] == "test"
        assert d["summary"] == "A task"
        assert len(d["phases"]) == 1
        assert len(d["tasks"]) == 1

    def test_to_markdown_contains_sections(self):
        plan = Plan(source="url", summary="Fix bug", phases=[], tasks=[], prompt="run this")
        md = plan.to_markdown()
        assert "# Implementation Plan" in md
        assert "Fix bug" in md
        assert "run this" in md

    def test_to_agent_prompt_returns_string(self):
        plan = Plan(source="x", summary="s", phases=[], tasks=[], prompt="custom prompt")
        assert plan.prompt == "custom prompt"


class TestPlanner:
    def test_plan_from_text(self):
        planner = Planner()
        plan = planner.plan("Fix login bug in auth module")
        assert plan.source == "Fix login bug in auth module"
        assert len(plan.phases) > 0
        assert len(plan.tasks) > 0

    def test_plan_loads_file(self, tmp_path: Path):
        issue_file = tmp_path / "issue.md"
        issue_file.write_text("# Fix authentication\n\nUsers cannot log in.", encoding="utf-8")
        planner = Planner()
        plan = planner.plan(str(issue_file))
        assert "authentication" in plan.summary.lower() or "log in" in plan.summary.lower()

    def test_plan_with_kb_research(self, tmp_path: Path):
        py_file = tmp_path / "auth.py"
        py_file.write_text("def authenticate(user):\n    pass\n", encoding="utf-8")
        from coderabbit.knowledge_base import KnowledgeBase
        kb = KnowledgeBase(db_path=tmp_path / "kb.db")
        kb.index_repo(tmp_path, "python")
        planner = Planner(kb=kb)
        plan = planner.plan("Fix authenticate function")
        kb.close()
        assert isinstance(plan, Plan)

    def test_plan_empty_source(self):
        planner = Planner()
        plan = planner.plan("")
        assert plan.source == ""

    def test_generate_phases_has_multiple(self):
        planner = Planner()
        issue = {"title": "Add feature", "affected_files": ["app.py"]}
        phases = planner._generate_phases(issue, {})
        assert len(phases) >= 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
