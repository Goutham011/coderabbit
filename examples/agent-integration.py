"""
Agent Integration Examples — How to use agentic CLI from coding agents.
"""

# ─────────────────────────────────────────────────────────────────────────────
# EXAMPLE 1: Hermes Agent calling agentic review
# ─────────────────────────────────────────────────────────────────────────────

import subprocess
import json


def review_with_hermes(repo: str, branch: str) -> dict:
    """Call agentic from Hermes agent."""
    result = subprocess.run(
        ["agentic", "review", repo, branch, "--output", "json"],
        capture_output=True,
        text=True,
    )
    
    if result.returncode != 0:
        return {"error": result.stderr, "status": "failed"}
    
    try:
        review = json.loads(result.stdout)
        return {
            "status": "success",
            "severity": review.get("overall_severity"),
            "findings_count": review.get("findings_count"),
            "confidence": review.get("confidence"),
            "top_findings": review.get("findings", [])[:5],
        }
    except json.JSONDecodeError:
        return {"error": "Invalid JSON output", "raw": result.stdout}


# Usage in Hermes:
# When user says "Review this PR" or when a new PR is detected:
# result = review_with_hermes("https://github.com/user/repo", "feature-branch")


# ─────────────────────────────────────────────────────────────────────────────
# EXAMPLE 2: Claude Code / Codex integration via MCP-style tool
# ─────────────────────────────────────────────────────────────────────────────

class AgenticTool:
    """
    Tool wrapper for coding agents to call agentic commands.
    Agents like Codex can invoke these methods directly.
    """
    
    def __init__(self):
        self.base_cmd = ["agentic"]
    
    def review(self, repo: str, branch: str, profile: str = "assertive") -> dict:
        """Run code review on a repository."""
        cmd = [*self.base_cmd, "review", repo, branch, "--output", "json", "--profile", profile]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return json.loads(result.stdout)
    
    def plan(self, source: str, format: str = "agent-prompt") -> dict:
        """Generate implementation plan."""
        cmd = [*self.base_cmd, "plan", source, "--output", format]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return json.loads(result.stdout)
    
    def verify(self, repo: str, branch: str, test_type: str = "unit") -> dict:
        """Sandbox test execution."""
        cmd = [*self.base_cmd, "verify", repo, branch, "--test-type", test_type]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return json.loads(result.stdout)


# Usage:
# tools = AgenticTool()
# review = tools.review("https://github.com/user/repo", "main")
# plan = tools.plan("Fix login bug")


# ─────────────────────────────────────────────────────────────────────────────
# EXAMPLE 3: OpenCode / Cursor extension using agentic
# ─────────────────────────────────────────────────────────────────────────────

# In openapi.json or similar agent config:
AGENTIC_TOOL_SPEC = {
    "name": "agentic_review",
    "description": "Run AI-powered code review on a repository branch",
    "parameters": {
        "type": "object",
        "properties": {
            "repo": {
                "type": "string",
                "description": "Repository URL (GitHub/GitLab) or local path"
            },
            "branch": {
                "type": "string", 
                "description": "Branch name or PR number"
            },
            "profile": {
                "type": "string",
                "enum": ["chill", "assertive", "quiet"],
                "default": "assertive",
                "description": "Review personality"
            }
        },
        "required": ["repo", "branch"]
    },
    "execute": "subprocess.run(['agentic', 'review', '{repo}', '{branch}', '--output', 'json', '--profile', '{profile}'], capture_output=True, text=True)"
}


# ─────────────────────────────────────────────────────────────────────────────
# EXAMPLE 4: Using agentic in a GitHub Action (CI/CD)
# ─────────────────────────────────────────────────────────────────────────────

# .github/workflows/agentic-review.yml
GITHUB_ACTION_YML = """
name: Agentic Code Review

on:
  pull_request:
    branches: [main, master]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Install agentic
        run: pip install agentic-cli
      
      - name: Run code review
        id: review
        run: |
          result=$(agentic review ${{ github.repository }} ${{ github.head_ref }} --output json)
          echo "$result" >> review-result.json
          severity=$(echo "$result" | jq -r '.overall_severity')
          echo "SEVERITY=$severity" >> $GITHUB_ENV
      
      - name: Check severity
        run: |
          if [ "$SEVERITY" = "critical" ]; then
            echo "::error::Critical findings detected — review required"
            exit 1
          fi
"""


# ─────────────────────────────────────────────────────────────────────────────
# EXAMPLE 5: Pre-commit hook integration
# ─────────────────────────────────────────────────────────────────────────────

# .pre-commit-config.yaml
PRE_COMMIT_CONFIG = """
repos:
  - repo: local
    hooks:
      - id: agentic-review
        name: agentic-review
        entry: agentic review
        language: system
        pass_filenames: false
        always_run: true
        args: ["--output", "human"]
"""


# ─────────────────────────────────────────────────────────────────────────────
# OUTPUT FORMAT SCHEMA
# ─────────────────────────────────────────────────────────────────────────────

# The CLI returns structured JSON that any agent can consume:

EXAMPLE_OUTPUT = """
{
  "repo": "https://github.com/user/repo",
  "branch": "feature-auth",
  "commit_sha": "abc123...",
  "overall_severity": "high",
  "findings_count": 3,
  "findings": [
    {
      "id": "semgrep-cwe-89",
      "tool": "semgrep",
      "rule": "python.lang.security.audit.sql-injection.sql-injection",
      "severity": "critical",
      "message": "Possible SQL injection via f-string",
      "file_path": "app/views.py",
      "line_number": 42,
      "suggestion": "Use parameterized queries instead of string formatting",
      "reference": "https://cwe.mitre.org/data/definitions/89.html"
    }
  ],
  "summary": "2 high-severity security issues found. Consider addressing before merge.",
  "confidence": 0.95,
  "metadata": {
    "profile": "assertive",
    "baseline": 0,
    "analyzers_run": 1
  }
}
"""


if __name__ == "__main__":
    # Demo usage
    print("Agentic CLI — Agent Integration Examples")
    print("=" * 50)
    print("\nThis module shows how coding agents can integrate with agentic.")
    print("See individual examples above for usage patterns.\n")
    
    # Quick demo
    import sys
    demo_result = subprocess.run(
        ["agentic", "token", "generate", "--scope", "read"],
        capture_output=True,
        text=True
    )
    print("Demo — Token Generation:")
    print(demo_result.stdout)
