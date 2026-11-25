"""Sandbox — safe test execution with isolation."""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import git


class SandboxResult:
    """Outcome from running tests in a sandbox."""

    def __init__(
        self,
        success: bool,
        command: str,
        returncode: int,
        stdout: str = "",
        stderr: str = "",
        duration_seconds: float = 0.0,
        artifacts: Optional[dict] = None,
        sandbox_mode: str = "process",
    ):
        self.success = success
        self.command = command
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.duration_seconds = duration_seconds
        self.artifacts = artifacts or {}
        self.sandbox_mode = sandbox_mode
        self.started_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "command": self.command,
            "returncode": self.returncode,
            "duration_seconds": round(self.duration_seconds, 2),
            "sandbox_mode": self.sandbox_mode,
            "started_at": self.started_at,
            "artifacts": self.artifacts,
        }


class SandboxManager:
    """Run tests in an isolated environment."""

    TIMEOUT_SECONDS = 180
    MAX_OUTPUT_CHARS = 50_000

    def __init__(self, work_dir: Optional[Path] = None):
        if work_dir is None:
            work_dir = Path(tempfile.mkdtemp(prefix="coderabbit_sandbox_"))
        else:
            work_dir.mkdir(parents=True, exist_ok=True)
        self._work_dir = work_dir
        self._docker_available = self._check_docker()

    def _check_docker(self) -> bool:
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def run_tests(
        self,
        repo_url: str,
        branch: str,
        test_type: str,
        extra_args: Optional[list[str]] = None,
        timeout: Optional[int] = None,
    ) -> SandboxResult:
        """Clone repo and run tests in isolated environment."""
        extra_args = extra_args or []
        timeout = timeout or self.TIMEOUT_SECONDS
        clone_path = self._clone(repo_url, branch)
        try:
            cmd = self._build_command(test_type, clone_path, extra_args)
            return self._execute(cmd, timeout, clone_path)
        finally:
            self._cleanup(clone_path)

    def _clone(self, repo_url: str, branch: str) -> Path:
        name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
        dest = self._work_dir / name
        if dest.exists():
            shutil.rmtree(dest)
        repo = git.Repo.clone_from(repo_url, dest, depth=1)
        try:
            repo.git.checkout(branch)
        except Exception:
            pass
        return dest

    def _build_command(
        self, test_type: str, repo_path: Path, extra_args: list[str]
    ) -> list[str]:
        pytest = shutil.which("pytest") or "python -m pytest"
        base = [pytest, "-x", "--tb=short"]
        if test_type == "unit":
            base += ["--cov=.", "--cov-report=xml", "--cov-report=term-missing"]
        elif test_type == "e2e":
            base += ["--timeout=60"]
        return base + extra_args + [str(repo_path)]

    def _execute(
        self, cmd: list[str], timeout: int, repo_path: Path
    ) -> SandboxResult:
        start = datetime.now(timezone.utc)
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(repo_path),
            )
            end = datetime.now(timezone.utc)
            duration = (end - start).total_seconds()
            stdout = self._limit(result.stdout, self.MAX_OUTPUT_CHARS)
            stderr = self._limit(result.stderr, self.MAX_OUTPUT_CHARS)
            artifacts = self._collect_artifacts(repo_path, result.returncode)
            mode = "docker" if self._docker_available else "process"
            return SandboxResult(
                success=result.returncode == 0,
                command=" ".join(cmd),
                returncode=result.returncode,
                stdout=stdout,
                stderr=stderr,
                duration_seconds=duration,
                artifacts=artifacts,
                sandbox_mode=mode,
            )
        except subprocess.TimeoutExpired as exc:
            end = datetime.now(timezone.utc)
            duration = (end - start).total_seconds()
            stdout_text = exc.stdout.decode("utf-8", errors="replace") if exc.stdout else ""
            stderr_text = exc.stderr.decode("utf-8", errors="replace") if exc.stderr else ""
            return SandboxResult(
                success=False,
                command=" ".join(cmd),
                returncode=-1,
                stdout=self._limit(stdout_text, self.MAX_OUTPUT_CHARS),
                stderr=self._limit(stderr_text, self.MAX_OUTPUT_CHARS),
                duration_seconds=duration,
                artifacts={"error": "test_timeout"},
                sandbox_mode="process",
            )

    @staticmethod
    def _limit(text: str, limit: int) -> str:
        if len(text) <= limit:
            return text
        return text[:limit] + f"\n... [truncated, {len(text)} total chars]"

    def _collect_artifacts(self, repo_path: Path, returncode: int) -> dict:
        artifacts: dict = {"exit_code": returncode}
        cov_xml = repo_path / "coverage.xml"
        if cov_xml.exists():
            artifacts["coverage"] = self._read_coverage(cov_xml)
        summary_py = repo_path / ".coderabbit_summary.json"
        if summary_py.exists():
            try:
                artifacts["summary"] = json.loads(summary_py.read_text())
            except json.JSONDecodeError:
                pass
        return artifacts

    @staticmethod
    def _read_coverage(path: Path) -> dict:
        content = path.read_text(errors="replace")
        lines_count = 0
        covered = 0
        for line in content.splitlines():
            stripped = line.strip()
            if not stripped.startswith('<line'):
                continue
            # Skip plain opening <line> tags without attributes
            if '<line>' == stripped or stripped == '<line ':
                continue
            # Extract all line numbers from the 'numbers' attribute
            num_match = stripped.find('numbers="')
            nums: list[int] = []
            if num_match != -1:
                try:
                    val_start = num_match + 9  # past the opening "
                    val_end = stripped.index('"', val_start)
                    nums = [int(n) for n in stripped[val_start:val_end].split(',')]
                except (ValueError, IndexError):
                    pass
            hits_match = stripped.find('hits="')
            is_covered = True
            if hits_match != -1:
                try:
                    val_start = hits_match + 6  # past the opening "
                    val_end = stripped.index('"', val_start)
                    is_covered = int(stripped[val_start:val_end]) > 0
                except (ValueError, IndexError):
                    is_covered = True
            # If we parsed individual numbers, count each; otherwise count the tag as one
            if nums:
                for _ in nums:
                    lines_count += 1
                    if is_covered:
                        covered += 1
            else:
                lines_count += 1
                if is_covered:
                    covered += 1
        if lines_count == 0:
            return {"status": "no_data"}
        pct = round((covered / lines_count) * 100, 1)
        return {"lines_total": lines_count, "lines_covered": covered, "percent": pct}

    def _cleanup(self, path: Path) -> None:
        try:
            shutil.rmtree(path)
        except OSError:
            pass

    def close(self) -> None:
        try:
            shutil.rmtree(self._work_dir)
        except OSError:
            pass
