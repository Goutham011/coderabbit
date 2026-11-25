"""Review engine — orchestrates analysis pipeline with multi-analyzer support and LLM-powered fixes."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, List, Dict, Any

import git

from .models import ReviewResult, Finding, Severity
from .config import Config
from .knowledge_base import KnowledgeBase


class ReviewEngine:
    """Main review engine with multi-analyzer support and LLM-powered fix generation."""

    def __init__(self, config_path: Optional[Path] = None, llm_provider: Optional[str] = None):
        self.config = Config.load(config_path)
        self._cache_dir = Path(tempfile.gettempdir()) / "agentic_cache"
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self.llm_provider = llm_provider or self._detect_llm_provider()
        self._llm_client = self._init_llm_client()

    def _detect_llm_provider(self) -> Optional[str]:
        """Auto-detect available LLM provider from environment or CLI agents."""
        # Check for local LLM servers
        if os.environ.get("OLLAMA_HOST") or Path("/usr/local/bin/ollama").exists() or Path.home().joinpath(".ollama").exists():
            return "ollama"
        if os.environ.get("LLAMA_CPP_SERVER") or Path("/usr/local/bin/llama-server").exists():
            return "llama.cpp"

        # Check for coding CLI agents
        if os.environ.get("CODEX_API_KEY") or shutil.which("codex"):
            return "codex"
        if os.environ.get("ANTHROPIC_API_KEY") or shutil.which("claude"):
            return "claude"
        if os.environ.get("OPENAI_API_KEY") or os.environ.get("HERMES_API_KEY"):
            return "openai-compatible"

        return None

    def _init_llm_client(self) -> Optional[Any]:
        """Initialize LLM client based on provider."""
        if not self.llm_provider:
            return None

        try:
            if self.llm_provider == "ollama":
                import ollama
                return ollama.Client()
            elif self.llm_provider == "llama.cpp":
                from llama_cpp import Llama
                return Llama(model_path=os.environ.get("LLAMA_MODEL_PATH", ""))
            elif self.llm_provider in ("codex", "claude", "openai-compatible"):
                import openai
                api_key = (
                    os.environ.get("CODEX_API_KEY")
                    or os.environ.get("ANTHROPIC_API_KEY")
                    or os.environ.get("OPENAI_API_KEY")
                    or os.environ.get("HERMES_API_KEY")
                )
                base_url = (
                    "https://api.codex.com/v1" if self.llm_provider == "codex"
                    else "https://api.anthropic.com/v1" if self.llm_provider == "claude"
                    else os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
                )
                return openai.OpenAI(api_key=api_key, base_url=base_url)
        except ImportError:
            pass
        return None

    def review(
        self,
        repo: str,
        branch: str = "HEAD",
        profile: str = "assertive",
        baseline: int = 0,
        full_scan: bool = False,
        apply_fixes: bool = False,
    ) -> ReviewResult:
        """Review a repository with optional full scan and fix generation."""
        is_local = Path(repo).is_absolute() or repo.startswith(("./", "../"))
        clone_path = self._ensure_local_repo(repo) if is_local else self._clone_repo(repo)
        kb = KnowledgeBase()
        try:
            if full_scan:
                findings = self._run_full_scan(clone_path)
            else:
                diff = self._get_diff(clone_path, branch)
                findings = self._run_analyzers(clone_path, diff)

            # Generate LLM-powered fixes
            if self._llm_client and findings:
                findings = self._generate_fixes(clone_path, findings)

            # Apply fixes if requested
            if apply_fixes and findings:
                self._apply_fixes(clone_path, findings)

            # Index for knowledge base (multi-language)
            languages = self._detect_languages(clone_path)
            for lang in languages:
                kb.index_repo(clone_path, lang)

            counts = {s.value: sum(1 for f in findings if f.severity == s) for s in Severity}
            overall = max(Severity, key=lambda s: counts[s.value]) if any(counts.values()) else Severity.INFO

            return ReviewResult(
                repo=repo,
                branch=branch,
                overall_severity=overall,
                findings=findings,
                confidence=min(1.0, 0.7 + len(findings) * 0.01),
                metadata={
                    "profile": profile,
                    "baseline": baseline,
                    "kb_indexed": True,
                    "languages": languages,
                    "full_scan": full_scan,
                    "llm_provider": self.llm_provider,
                    "fixes_generated": any(f.suggestion for f in findings),
                },
            )
        finally:
            kb.close()
            if not is_local:
                self._cleanup_repo(clone_path)

    def _detect_languages(self, repo_path: Path) -> List[str]:
        """Detect programming languages in repository."""
        extensions = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "javascript",
            ".tsx": "typescript",
            ".java": "java",
            ".go": "go",
            ".rs": "rust",
            ".cpp": "cpp",
            ".cc": "cpp",
            ".c": "c",
            ".h": "c",
            ".hpp": "cpp",
            ".cs": "csharp",
            ".rb": "ruby",
            ".php": "php",
            ".swift": "swift",
            ".kt": "kotlin",
            ".scala": "scala",
        }
        found = set()
        for ext, lang in extensions.items():
            if list(repo_path.rglob(f"*{ext}")):
                found.add(lang)
        return list(found) or ["python"]

    def _run_full_scan(self, repo_path: Path) -> List[Finding]:
        """Run analyzers on all files (not just diff)."""
        findings: List[Finding] = []
        if self.config.tools.semgrep:
            findings.extend(self._run_semgrep_full(repo_path))
        if self.config.tools.eslint:
            findings.extend(self._run_eslint(repo_path))
        if self.config.tools.pylint:
            findings.extend(self._run_pylint(repo_path))
        if self.config.tools.bandit:
            findings.extend(self._run_bandit(repo_path))
        for rule_file in self.config.tools.custom_rules:
            findings.extend(self._run_custom_rules(repo_path, rule_file))
        return findings

    def _run_analyzers(self, repo_path: Path, diff: str) -> List[Finding]:
        """Run analyzers on diff (original behavior)."""
        findings: List[Finding] = []
        if self.config.tools.semgrep:
            findings.extend(self._run_semgrep(repo_path, diff))
        if self.config.tools.eslint:
            findings.extend(self._run_eslint_diff(repo_path, diff))
        if self.config.tools.pylint:
            findings.extend(self._run_pylint_diff(repo_path, diff))
        if self.config.tools.bandit:
            findings.extend(self._run_bandit_diff(repo_path, diff))
        for rule_file in self.config.tools.custom_rules:
            findings.extend(self._run_custom_rules_diff(repo_path, diff, rule_file))
        return findings

    # ===== Semgrep =====
    def _run_semgrep(self, repo_path: Path, diff: str) -> List[Finding]:
        """Run semgrep on diff via stdin."""
        try:
            result = subprocess.run(
                ["semgrep", "--json", "--no-config", "-"],
                input=diff,
                capture_output=True,
                text=True,
                cwd=str(repo_path),
                timeout=120,
            )
            if result.returncode not in (0, 1):
                return []
            data = json.loads(result.stdout)
            return [
                Finding(
                    id=f"semgrep-{m.get('check_id', 'unknown')}",
                    tool="semgrep",
                    rule=m.get("check_id"),
                    severity=self._map_severity(m.get("extra", {}).get("severity")),
                    message=m.get("extra", {}).get("message", ""),
                    file_path=m.get("path"),
                    line_number=m.get("start", {}).get("line"),
                    reference=m.get("extra", {}).get("metadata", {}).get("cwe", "").split(":")[-1],
                )
                for m in data.get("results", [])
            ]
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            return []

    def _run_semgrep_full(self, repo_path: Path) -> List[Finding]:
        """Run semgrep on entire repository."""
        try:
            result = subprocess.run(
                ["semgrep", "--json", "--no-config", "."],
                capture_output=True,
                text=True,
                cwd=str(repo_path),
                timeout=300,
            )
            if result.returncode not in (0, 1):
                return []
            data = json.loads(result.stdout)
            return [
                Finding(
                    id=f"semgrep-{m.get('check_id', 'unknown')}",
                    tool="semgrep",
                    rule=m.get("check_id"),
                    severity=self._map_severity(m.get("extra", {}).get("severity")),
                    message=m.get("extra", {}).get("message", ""),
                    file_path=m.get("path"),
                    line_number=m.get("start", {}).get("line"),
                    reference=m.get("extra", {}).get("metadata", {}).get("cwe", "").split(":")[-1],
                )
                for m in data.get("results", [])
            ]
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            return []

    # ===== ESLint =====
    def _run_eslint(self, repo_path: Path) -> List[Finding]:
        """Run ESLint on entire JS/TS project."""
        return self._run_linter(
            repo_path,
            ["eslint", "--format", "json", "."],
            "eslint",
            self._parse_eslint,
        )

    def _run_eslint_diff(self, repo_path: Path, diff: str) -> List[Finding]:
        """Run ESLint only on changed files from diff."""
        changed_files = self._extract_changed_files(diff, [".js", ".ts", ".jsx", ".tsx"])
        if not changed_files:
            return []
        return self._run_linter(
            repo_path,
            ["eslint", "--format", "json"] + changed_files,
            "eslint",
            self._parse_eslint,
        )

    def _parse_eslint(self, output: str, repo_path: Path) -> List[Finding]:
        try:
            data = json.loads(output)
            findings = []
            for file_result in data:
                for msg in file_result.get("messages", []):
                    findings.append(
                        Finding(
                            id=f"eslint-{msg.get('ruleId', 'unknown')}",
                            tool="eslint",
                            rule=msg.get("ruleId"),
                            severity=self._map_eslint_severity(msg.get("severity")),
                            message=msg.get("message", ""),
                            file_path=file_result.get("filePath", "").replace(str(repo_path) + "/", ""),
                            line_number=msg.get("line"),
                            reference=msg.get("ruleId"),
                        )
                    )
            return findings
        except json.JSONDecodeError:
            return []

    # ===== Pylint =====
    def _run_pylint(self, repo_path: Path) -> List[Finding]:
        """Run Pylint on entire Python project."""
        return self._run_linter(
            repo_path,
            ["pylint", "--output-format=json", "."],
            "pylint",
            self._parse_pylint,
        )

    def _run_pylint_diff(self, repo_path: Path, diff: str) -> List[Finding]:
        """Run Pylint only on changed Python files."""
        changed_files = self._extract_changed_files(diff, [".py"])
        if not changed_files:
            return []
        return self._run_linter(
            repo_path,
            ["pylint", "--output-format=json"] + changed_files,
            "pylint",
            self._parse_pylint,
        )

    def _parse_pylint(self, output: str, repo_path: Path) -> List[Finding]:
        try:
            data = json.loads(output)
            findings = []
            for msg in data:
                findings.append(
                    Finding(
                        id=f"pylint-{msg.get('message-id', 'unknown')}",
                        tool="pylint",
                        rule=msg.get("message-id"),
                        severity=self._map_pylint_severity(msg.get("type")),
                        message=msg.get("message", ""),
                        file_path=msg.get("path", "").replace(str(repo_path) + "/", ""),
                        line_number=msg.get("line"),
                        reference=msg.get("symbol"),
                    )
                )
            return findings
        except json.JSONDecodeError:
            return []

    # ===== Bandit =====
    def _run_bandit(self, repo_path: Path) -> List[Finding]:
        """Run Bandit on entire Python project."""
        return self._run_linter(
            repo_path,
            ["bandit", "-r", ".", "-f", "json"],
            "bandit",
            self._parse_bandit,
        )

    def _run_bandit_diff(self, repo_path: Path, diff: str) -> List[Finding]:
        """Run Bandit only on changed Python files."""
        changed_files = self._extract_changed_files(diff, [".py"])
        if not changed_files:
            return []
        # Bandit doesn't support file list easily, run on whole repo but filter
        findings = self._run_bandit(repo_path)
        return [f for f in findings if f.file_path in changed_files]

    def _parse_bandit(self, output: str, repo_path: Path) -> List[Finding]:
        try:
            data = json.loads(output)
            findings = []
            for msg in data.get("results", []):
                findings.append(
                    Finding(
                        id=f"bandit-{msg.get('test_id', 'unknown')}",
                        tool="bandit",
                        rule=msg.get("test_id"),
                        severity=self._map_bandit_severity(msg.get("issue_severity")),
                        message=msg.get("issue_text", ""),
                        file_path=msg.get("filename", "").replace(str(repo_path) + "/", ""),
                        line_number=msg.get("line_number"),
                        reference=msg.get("test_id"),
                    )
                )
            return findings
        except json.JSONDecodeError:
            return []

    # ===== Custom Rules =====
    def _run_custom_rules(self, repo_path: Path, rule_file: str) -> List[Finding]:
        """Run semgrep with custom rule file."""
        try:
            result = subprocess.run(
                ["semgrep", "--json", "--config", rule_file, "."],
                capture_output=True,
                text=True,
                cwd=str(repo_path),
                timeout=120,
            )
            if result.returncode not in (0, 1):
                return []
            data = json.loads(result.stdout)
            return [
                Finding(
                    id=f"custom-{m.get('check_id', 'unknown')}",
                    tool="custom",
                    rule=m.get("check_id"),
                    severity=self._map_severity(m.get("extra", {}).get("severity")),
                    message=m.get("extra", {}).get("message", ""),
                    file_path=m.get("path"),
                    line_number=m.get("start", {}).get("line"),
                    reference=m.get("extra", {}).get("metadata", {}).get("cwe", "").split(":")[-1],
                )
                for m in data.get("results", [])
            ]
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            return []

    def _run_custom_rules_diff(self, repo_path: Path, diff: str, rule_file: str) -> List[Finding]:
        """Run custom semgrep rules on diff."""
        try:
            result = subprocess.run(
                ["semgrep", "--json", "--config", rule_file, "-"],
                input=diff,
                capture_output=True,
                text=True,
                cwd=str(repo_path),
                timeout=120,
            )
            if result.returncode not in (0, 1):
                return []
            data = json.loads(result.stdout)
            return [
                Finding(
                    id=f"custom-{m.get('check_id', 'unknown')}",
                    tool="custom",
                    rule=m.get("check_id"),
                    severity=self._map_severity(m.get("extra", {}).get("severity")),
                    message=m.get("extra", {}).get("message", ""),
                    file_path=m.get("path"),
                    line_number=m.get("start", {}).get("line"),
                    reference=m.get("extra", {}).get("metadata", {}).get("cwe", "").split(":")[-1],
                )
                for m in data.get("results", [])
            ]
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            return []

    # ===== Helper Methods =====
    def _run_linter(self, repo_path: Path, cmd: List[str], tool: str, parser) -> List[Finding]:
        """Generic linter runner."""
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(repo_path), timeout=120)
            if result.returncode not in (0, 1, 2, 32):  # Common non-error codes
                return []
            return parser(result.stdout, repo_path)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return []

    def _extract_changed_files(self, diff: str, extensions: List[str]) -> List[str]:
        """Extract changed file paths from diff matching extensions."""
        files = []
        for line in diff.splitlines():
            if line.startswith("+++ b/") or line.startswith("--- a/"):
                path = line[6:]
                if any(path.endswith(ext) for ext in extensions):
                    files.append(path)
        return list(set(files))

    # ===== Severity Mapping =====
    def _map_severity(self, s: str) -> Severity:
        return {"ERROR": Severity.HIGH, "WARNING": Severity.MEDIUM, "INFO": Severity.LOW}.get(s.upper(), Severity.INFO)

    def _map_eslint_severity(self, s: int) -> Severity:
        return {2: Severity.HIGH, 1: Severity.MEDIUM, 0: Severity.LOW}.get(s, Severity.INFO)

    def _map_pylint_severity(self, s: str) -> Severity:
        return {"error": Severity.HIGH, "warning": Severity.MEDIUM, "refactor": Severity.LOW, "convention": Severity.INFO, "info": Severity.INFO}.get(s.lower(), Severity.INFO)

    def _map_bandit_severity(self, s: str) -> Severity:
        return {"HIGH": Severity.HIGH, "MEDIUM": Severity.MEDIUM, "LOW": Severity.LOW}.get(s.upper(), Severity.INFO)

    # ===== LLM-Powered Fix Generation =====
    def _generate_fixes(self, repo_path: Path, findings: List[Finding]) -> List[Finding]:
        """Generate fix suggestions using LLM."""
        if not self._llm_client:
            return findings

        # Group findings by file for context
        by_file: Dict[str, List[Finding]] = {}
        for f in findings:
            if f.file_path:
                by_file.setdefault(f.file_path, []).append(f)

        for file_path, file_findings in by_file.items():
            full_path = repo_path / file_path
            if not full_path.exists():
                continue

            try:
                content = full_path.read_text(encoding="utf-8", errors="replace")
                suggestions = self._get_llm_fixes(file_path, content, file_findings)
                for finding, suggestion in zip(file_findings, suggestions):
                    finding.suggestion = suggestion
            except Exception:
                pass

        return findings

    def _get_llm_fixes(self, file_path: str, content: str, findings: List[Finding]) -> List[str]:
        """Get fix suggestions from LLM."""
        findings_text = "\n".join(
            f"- Line {f.line_number}: [{f.severity.value}] {f.message} (rule: {f.rule})"
            for f in findings
        )

        prompt = f"""You are a senior code reviewer. Fix the following issues in this {Path(file_path).suffix} file.

File: {file_path}
Issues:
{findings_text}

Code:
```{Path(file_path).suffix[1:]}
{content}
```

Return ONLY the fixed code block with the same language marker. No explanations."""

        try:
            if self.llm_provider == "ollama":
                response = self._llm_client.chat(
                    model=os.environ.get("OLLAMA_MODEL", "codellama:13b"),
                    messages=[{"role": "user", "content": prompt}],
                    options={"temperature": 0.1, "num_predict": 4096},
                )
                return [self._extract_code_block(response["message"]["content"])] * len(findings)

            elif self.llm_provider == "llama.cpp":
                response = self._llm_client(prompt, max_tokens=4096, temperature=0.1, stop=["```"])
                return [self._extract_code_block(response["choices"][0]["text"])] * len(findings)

            else:  # OpenAI-compatible (codex, claude, openai)
                response = self._llm_client.chat.completions.create(
                    model=os.environ.get("LLM_MODEL", "gpt-4o"),
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=4096,
                )
                return [self._extract_code_block(response.choices[0].message.content)] * len(findings)

        except Exception:
            return [""] * len(findings)

    def _extract_code_block(self, text: str) -> str:
        """Extract code from markdown code block."""
        match = re.search(r"```(?:\w+)?\n(.*?)\n```", text, re.DOTALL)
        return match.group(1).strip() if match else text.strip()

    def _apply_fixes(self, repo_path: Path, findings: List[Finding]) -> int:
        """Apply fix suggestions to files. Returns count of applied fixes."""
        applied = 0
        by_file: Dict[str, List[Finding]] = {}
        for f in findings:
            if f.file_path and f.suggestion:
                by_file.setdefault(f.file_path, []).append(f)

        for file_path, file_findings in by_file.items():
            full_path = repo_path / file_path
            if not full_path.exists():
                continue

            try:
                content = full_path.read_text(encoding="utf-8", errors="replace")
                lines = content.splitlines()

                # Apply fixes in reverse line order to preserve line numbers
                for finding in sorted(file_findings, key=lambda f: f.line_number or 0, reverse=True):
                    if finding.line_number and finding.suggestion:
                        idx = finding.line_number - 1
                        if 0 <= idx < len(lines):
                            lines[idx] = finding.suggestion
                            applied += 1

                full_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            except Exception:
                pass

        return applied

    # ===== Git Operations =====
    def _ensure_local_repo(self, path: str) -> Path:
        p = Path(path)
        if not (p / ".git").exists():
            raise ValueError(f"Not a git repository: {path}")
        return p

    def _clone_repo(self, repo_url: str) -> Path:
        name = repo_url.split("/")[-1].replace(".git", "")
        path = self._cache_dir / name
        if not path.exists():
            git.Repo.clone_from(repo_url, path)
        return path

    def _get_diff(self, repo_path: Path, branch: str) -> str:
        repo = git.Repo(repo_path)
        try:
            if branch.isdigit():
                remote = repo.remotes.origin
                pr_ref = f"pull/{branch}/head"
                remote.fetch(refspec=pr_ref, depth=1)
                return repo.git.diff(f"origin/main...{pr_ref}")
            return repo.git.diff("origin/main...", branch)
        except Exception:
            return repo.git.diff("HEAD~1", "HEAD")

    def _cleanup_repo(self, repo_path: Path) -> None:
        try:
            shutil.rmtree(repo_path)
        except Exception:
            pass