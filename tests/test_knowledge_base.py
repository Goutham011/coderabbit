"""Tests for knowledge graph."""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from agentic.knowledge_base import KnowledgeBase


class TestKnowledgeBase:
    def test_initializes_db(self, tmp_path: Path):
        kb = KnowledgeBase(db_path=tmp_path / "test.db")
        assert (tmp_path / "test.db").exists()
        kb.close()

    def test_index_file_creates_nodes(self, tmp_path: Path):
        py_file = tmp_path / "test.py"
        py_file.write_text("def hello():\n    pass\n\nclass Foo:\n    pass\n", encoding="utf-8")
        kb = KnowledgeBase(db_path=tmp_path / "test.db")
        result = kb.index_repo(tmp_path, "python")
        assert result["files_indexed"] >= 1
        kb.close()

    def test_query_returns_results(self, tmp_path: Path):
        py_file = tmp_path / "app.py"
        py_file.write_text("def process_data(x):\n    return x * 2\n", encoding="utf-8")
        kb = KnowledgeBase(db_path=tmp_path / "test.db")
        kb.index_repo(tmp_path, "python")
        results = kb.query("file", "app.py")
        assert len(results) > 0
        kb.close()

    def test_close_does_not_crash(self, tmp_path: Path):
        kb = KnowledgeBase(db_path=tmp_path / "test.db")
        kb.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
