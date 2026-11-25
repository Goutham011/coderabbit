"""Tests for the review engine."""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from agentic.models import Finding, Severity, ReviewResult
from agentic.config import Config


class TestFinding:
    def test_finding_to_dict(self):
        finding = Finding(
            id="test-1", tool="semgrep", severity=Severity.HIGH,
            message="Possible SQL injection", file_path="app.py", line_number=42,
        )
        d = finding.to_dict()
        assert d["id"] == "test-1"
        assert d["severity"] == "high"
        assert d["file_path"] == "app.py"


class TestConfig:
    def test_default_config(self):
        config = Config()
        assert config.version == 1
        assert config.reviews.profile == "assertive"
        assert config.tools.semgrep is True

    def test_config_from_dict(self):
        data = {"version": 1, "language": "python", "reviews": {"profile": "chill"}, "tools": {"semgrep": False}}
        config = Config(**data)
        assert config.language == "python"
        assert config.reviews.profile == "chill"
        assert config.tools.semgrep is False


class TestReviewEngine:
    @patch("agentic.review.git.Repo")
    def test_review_local_repo(self, mock_git_cls):
        from agentic.review import ReviewEngine
        mock_repo = Mock()
        mock_repo.git.diff.return_value = "diff --git a/test.py b/test.py\n+print('hello')\n"
        mock_git_cls.return_value = mock_repo
        engine = ReviewEngine()
        with patch.object(engine, '_run_analyzers', return_value=[]):
            result = engine.review(".", "main")
            assert isinstance(result, ReviewResult)
            assert result.branch == "main"

    def test_severity_mapping(self):
        from agentic.review import ReviewEngine
        engine = ReviewEngine()
        assert engine._map_severity("ERROR") == Severity.HIGH
        assert engine._map_severity("WARNING") == Severity.MEDIUM
        assert engine._map_severity("INFO") == Severity.LOW
        assert engine._map_severity("UNKNOWN") == Severity.INFO


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
