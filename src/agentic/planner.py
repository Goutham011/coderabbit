"""Planning engine — generates implementation plans from issues or specs.

SECURITY: This module validates URLs before fetching to prevent SSRF attacks.
Only HTTP/HTTPS URLs from allowlisted domains are permitted.
"""
from __future__ import annotations

import re
import json
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

# SECURITY: Configuration for allowed domains (SSRF protection)
ALLOWED_DOMAINS = [
    'github.com',
    'gitlab.com',
    'bitbucket.org',
    'jira.atlassian.com',
    'asana.com',
    'linear.app',
    'trello.com',
]

# SECURITY: Blocked URL schemes that could be used for SSRF
BLOCKED_SCHEMES = ['file', 'ftp', 'sftp', 'ssh', 'gopher', 'dict', 'ldap', 'ldapldif']


def _is_url_safe(url: str) -> bool:
    """Validate URL to prevent SSRF attacks."""
    try:
        parsed = urlparse(url)
        
        # Only allow http and https schemes
        if parsed.scheme.lower() not in ('http', 'https'):
            return False
        
        # Check for blocked host patterns (localhost, internal IPs, etc.)
        hostname = parsed.hostname or ''
        blocked_hosts = ['localhost', '127.0.0.1', '0.0.0.0', '::1', '169.254.169.254']  # nosec B104
        if hostname.lower() in blocked_hosts:
            return False
        
        # Check for internal IP ranges
        if hostname.startswith('192.168.') or hostname.startswith('10.') or hostname.startswith('172.'):
            # Allow if in allowlist
            domain_allowed = any(hostname.endswith(domain) for domain in ALLOWED_DOMAINS)
            if not domain_allowed:
                return False
        
        # Check domain allowlist
        domain_allowed = any(
            hostname == domain or hostname.endswith(f'.{domain}')
            for domain in ALLOWED_DOMAINS
        )
        
        return domain_allowed
    except Exception:
        return False


class Plan:
    """Structured implementation plan."""

    def __init__(self, source: str, summary: str = "", phases: list[dict] | None = None, tasks: list[str] | None = None, prompt: str = ""):
        self.source = source
        self.summary = summary
        self.phases = phases or []
        self.tasks = tasks or []
        self.prompt = prompt

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "summary": self.summary,
            "phases": self.phases,
            "tasks": self.tasks,
            "prompt": self.prompt,
        }

    def to_markdown(self) -> str:
        lines = [f"# Implementation Plan", "", f"**Source:** {self.source}", "", f"## Summary", "", self.summary, ""]
        if self.phases:
            lines.append("## Phases")
            for i, phase in enumerate(self.phases, 1):
                lines.extend(["", f"### Phase {i}: {phase.get('title', '')}", "", phase.get("description", ""), ""])
        if self.tasks:
            lines.extend(["", "## Tasks", ""])
            for task in self.tasks:
                lines.append(f"- [ ] {task}")
        if self.prompt:
            lines.extend(["", "## Agent Prompt", "", "```", self.prompt, "```"])
        return "\n".join(lines)


class Planner:
    """Generate implementation plans from issues or specifications."""

    def __init__(self, kb=None):
        self._kb = kb

    def plan(self, source: str, output_format: str = "json") -> Plan:
        """Create plan from issue URL, file path, or text description."""
        source_text = self._load_source(source)
        issue_data = self._parse_issue(source_text)
        research = self._research(issue_data)
        phases = self._generate_phases(issue_data, research)
        tasks = self._extract_tasks(phases)
        prompt = self._build_prompt(issue_data, phases, tasks)
        return Plan(
            source=source,
            summary=issue_data.get("summary", ""),
            phases=phases,
            tasks=tasks,
            prompt=prompt,
        )

    def _load_source(self, source: str) -> str:
        """Load source content from URL or file.
        
        SECURITY: URLs are validated before fetching to prevent SSRF attacks.
        """
        if not source:
            return ""
        if source.startswith(("http://", "https://")):
            # SECURITY: Validate URL to prevent SSRF
            if not _is_url_safe(source):
                return f"Issue source: {source} (URL blocked for security reasons)"
            try:
                import urllib.request
                # SECURITY: URL has been validated by _is_url_safe() above
                # only http/https URLs from allowlisted domains can reach here
                with urllib.request.urlopen(source, timeout=10) as resp:  # nosec B310
                    return resp.read().decode("utf-8", errors="replace")
            except Exception:
                return f"Issue source: {source}"
        path = Path(source)
        if path.exists() and path.is_file():
            return path.read_text(encoding="utf-8", errors="replace")
        return source

    def _parse_issue(self, text: str) -> dict:
        """Extract structured data from issue/spec text."""
        title_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else "Implementation Task"
        summary = text[:500] if len(text) > 500 else text
        keywords = set(re.findall(r"\b\w{4,}\b", text.lower()))
        files = re.findall(r"`([^`]+\.py)`|(\S+\.py)", text)
        affected_files = [m[0] or m[1] for m in files] if files else []
        return {"title": title, "summary": summary, "keywords": list(keywords), "affected_files": affected_files}

    def _research(self, issue_data: dict) -> dict:
        """Query knowledge base for related code."""
        if self._kb is None:
            return {"related_symbols": [], "related_files": []}
        related_symbols = []
        related_files = []
        for keyword in issue_data.get("keywords", [])[:5]:
            symbols = self._kb.query("def", keyword)
            related_symbols.extend(symbols)
            files = self._kb.query("file", keyword)
            related_files.extend(files)
        return {"related_symbols": related_symbols[:10], "related_files": related_files[:10]}

    def _generate_phases(self, issue_data: dict, research: dict) -> list[dict]:
        """Create phased implementation plan."""
        phases = []
        title = issue_data.get("title", "Task")
        affected = issue_data.get("affected_files", [])
        phases.append({
            "title": f"Research and Setup",
            "description": f"Review existing codebase for {title}. Check affected modules: {', '.join(affected[:3]) or 'none specified'}.",
        })
        if research.get("related_symbols"):
            phases.append({
                "title": "Understand Dependencies",
                "description": f"Analyze {len(research['related_symbols'])} related functions. Map call chains and data flow.",
            })
        phases.append({"title": "Implement Core Logic", "description": "Write the primary implementation following project conventions."})
        phases.append({"title": "Add Tests", "description": "Cover normal paths, edge cases, and error conditions."})
        phases.append({"title": "Verify and Document", "description": "Run tests. Update documentation if public API changed."})
        return phases

    def _extract_tasks(self, phases: list[dict]) -> list[str]:
        """Convert phases to checklist items."""
        tasks = []
        for phase in phases:
            tasks.append(f"[ ] {phase['title']}")
        return tasks

    def _build_prompt(self, issue_data: dict, phases: list[dict], tasks: list[str]) -> str:
        """Generate agent-ready prompt."""
        title = issue_data.get("title", "Task")
        prompt_lines = [f"Implement: {title}", ""]
        prompt_lines.append("Context:")
        for phase in phases:
            prompt_lines.append(f"- {phase['title']}: {phase['description']}")
        prompt_lines.append("")
        prompt_lines.append("Tasks:")
        for task in tasks:
            prompt_lines.append(task)
        return "\n".join(prompt_lines)
