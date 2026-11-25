# Agentic CLI — Code Review System for AI Agents

CLI-first code review engine designed to integrate with coding agents (Hermes, Claude Code, Codex, OpenCode).

## Philosophy

- **Agent-native**: JSON output by default, easy to parse in any language
- **Offline-capable**: Cache repos locally, work without network
- **Configurable**: `.agentic.yaml` for per-repo settings
- **Extensible**: Plugin system for custom analyzers

## Quick Start

```bash
# Install
pip install -e .

# Generate token for API access
agentic token generate --scope read

# Review a branch (JSON output for agents)
agentic review https://github.com/org/repo main --output json

# Human-readable review
agentic review ./my-project feature-branch --output human

# Plan from an issue
agentic plan https://github.com/org/repo/issues/42 --output agent-prompt
```

## Agent Integration Example

```python
# Hermes or any agent calling agentic
import subprocess
import json

result = subprocess.run(
    ["agentic", "review", "https://github.com/user/repo", "feature-branch", "--output", "json"],
    capture_output=True, text=True
)

review = json.loads(result.stdout)
print(review["findings"])  # Structured findings
```

## Commands

| Command | Description |
|---------|-------------|
| `review <repo> <branch>` | Analyze code changes |
| `plan <source>` | Generate implementation plan |
| `verify <repo> <branch>` | Sandbox test execution |
| `triage` | Priority queue of open PRs |
| `token generate` | Create auth token |

## Configuration

Create `.agentic.yaml` in your repo root:

```yaml
version: 1
language: python
reviews:
  profile: assertive
  auto_review: true
tools:
  semgrep: enabled
  eslint: enabled
knowledge_base:
  guidelines: docs/coding-standards.md
unsafe_symbols:
  - eval(
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Lint
ruff check src/
```

## Architecture

See [architecture-open.md](./architecture-open.md) for full system design.
