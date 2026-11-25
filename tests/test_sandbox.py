"""Tests for the sandbox module."""
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from coderabbit.sandbox import SandboxManager, SandboxResult


class TestSandboxResult:
    def test_default_artifacts_is_empty_dict(self):
        r = SandboxResult(success=True, command="pytest", returncode=0)
        assert r.artifacts == {}

    def test_to_dict_contains_expected_keys(self):
        r = SandboxResult(success=False, command="run", returncode=1,
                          duration_seconds=3.5)
        d = r.to_dict()
        assert d["success"] is False
        assert d["command"] == "run"
        assert d["returncode"] == 1
        assert d["duration_seconds"] == 3.5
        assert "started_at" in d
        assert "sandbox_mode" in d
        assert isinstance(d["artifacts"], dict)

    def test_success_true_means_zero_returncode(self):
        r = SandboxResult(success=True, command="ok", returncode=0)
        assert r.success is True

    def test_success_false_means_nonzero_returncode(self):
        r = SandboxResult(success=False, command="fail", returncode=2)
        assert r.success is False


class TestSandboxManagerInit:
    def test_work_dir_created(self, tmp_path):
        mgr = SandboxManager(work_dir=tmp_path / "sandbox_test")
        try:
            assert (tmp_path / "sandbox_test").exists()
        finally:
            mgr.close()

    def test_docker_not_available_when_no_binary(self):
        mgr = SandboxManager()
        try:
            with patch("subprocess.run", side_effect=FileNotFoundError):
                assert mgr._check_docker() is False
        finally:
            mgr.close()


class TestBuildCommand:
    def test_unit_type_includes_coverage(self):
        mgr = SandboxManager()
        try:
            cmd = mgr._build_command("unit", Path("/tmp"), [])
            assert "--cov=." in cmd
        finally:
            mgr.close()

    def test_e2e_type_includes_timeout_flag(self):
        mgr = SandboxManager()
        try:
            cmd = mgr._build_command("e2e", Path("/tmp"), [])
            assert "--timeout=60" in cmd
        finally:
            mgr.close()

    def test_integration_type_has_no_extra_flags(self):
        mgr = SandboxManager()
        try:
            cmd = mgr._build_command("integration", Path("/tmp"), [])
            assert "--cov=." not in cmd
            assert "--timeout" not in cmd
        finally:
            mgr.close()

    def test_extra_args_appended(self):
        mgr = SandboxManager()
        try:
            cmd = mgr._build_command("unit", Path("/tmp"), ["-k", "auth"])
            assert "-k" in cmd
            assert "auth" in cmd
        finally:
            mgr.close()


class TestLimit:
    def test_short_string_returns_unchanged(self):
        mgr = SandboxManager()
        try:
            out = mgr._limit("hello", 100)
            assert out == "hello"
        finally:
            mgr.close()

    def test_long_string_gets_truncated_with_notice(self):
        mgr = SandboxManager()
        long_str = "x" * 200
        out = mgr._limit(long_str, 100)
        assert len(out) < 200
        assert "truncated" in out
        mgr.close()


class TestCollectArtifacts:
    def test_missing_coverage_file_returns_exit_code_only(self):
        mgr = SandboxManager()
        artifacts = mgr._collect_artifacts(Path("/nonexistent"), 0)
        assert "exit_code" in artifacts
        mgr.close()

    def test_read_coverage_parses_valid_xml(self, tmp_path):
        xml_content = (
            '<?xml version="1.0" ?>\n'
            '<coverage><sources><source>.</source></sources>\n'
            '<package name="tests"><file name="test_a.py">\n'
            '<line numbers="1,2,3,5" hits="1"/>\n'
            '<line numbers="4" hits="0"/>\n'
            '</file></package></coverage>'
        )
        cov_path = tmp_path / "coverage.xml"
        cov_path.write_text(xml_content)
        mgr = SandboxManager()
        artifacts = mgr._collect_artifacts(tmp_path, 0)
        mgr.close()
        assert "coverage" in artifacts
        assert artifacts["coverage"]["percent"] == 80.0


class TestCleanup:
    def test_cleanup_removes_path(self, tmp_path):
        mgr = SandboxManager()
        sub = tmp_path / "to_remove"
        sub.mkdir()
        mgr._cleanup(sub)
        assert not sub.exists()
        mgr.close()

    def test_cleanup_handles_missing_path(self, tmp_path):
        mgr = SandboxManager()
        mgr._cleanup(tmp_path / "does_not_exist")
        mgr.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
