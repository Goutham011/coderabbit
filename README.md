<p align="center">
  <img src="assets/app_icon.svg" width="150" alt="Coderabbit Logo" />
</p>

<h1 align="center">Coderabbit</h1>

<p align="center">
  <strong>Code review for AI agents — CLI-first, offline-capable, extensible.</strong><br>
  A sophisticated code review system that lets your AI coding agent understand context, find issues, and write better code.
</p>

<p align="center">
  <strong>English</strong>
</p>

<p align="center">
  <a href="https://github.com/Goutham011/coderabbit/stargazers"><img src="https://img.shields.io/github/stars/Goutham011/coderabbit?style=flat-square&color=gold" alt="GitHub stars" /></a>
  <a href="https://github.com/Goutham011/coderabbit/releases/latest"><img src="https://img.shields.io/github/v/release/Goutham011/coderabbit?style=flat-square&color=blue" alt="Latest release" /></a>
  <img src="https://img.shields.io/badge/platform-Python%203.9%2B-lightgrey?style=flat-square" alt="Python 3.9+" />
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="MIT License" />
</p>

---

## Why Coderabbit?

AI coding agents need to understand code deeply to write quality software. Coderabbit provides the context and analysis they need to review their own work and catch issues before they become bugs.

- **Agent-native.** JSON output by default, easy to parse in any language (Python, JavaScript, Go, etc.)
- **Offline-capable.** Cache repos locally, work without network access to external services
- **Privacy-first.** Your code never leaves your machine unless you configure it to
- **Configurable.** `.coderabbit.yaml` for per-repo settings, team-wide policies
- **Extensible.** Plugin system for custom analyzers, linter integrations, and domain-specific rules
- **Tool-focused.** Understands 15+ tools: semgrep, eslint, ruff, mypy, bandit, and more

---

## Features at a glance

<table>
<tr>
<td width="33%" valign="top">

### 🔍 Review
- **Branch analysis** — Diff-based code review for any branch
- **Multi-tool scanning** — Semgrep, ESLint, Ruff, MyPy, Bandit
- **Security checks** — Detects secrets, vulnerabilities, unsafe patterns
- **Style guide** — Enforces team coding standards

</td>
<td width="33%" valign="top">

### 🧠 Planning
- **Issue-to-plan** — Convert GitHub issues into implementation plans
- **PR triage** — Automatic priority queue for open pull requests
- **Risk assessment** — Estimate complexity, test coverage needs

</td>
<td width="33%" valign="top">

### 🛡️ Verification
- **Sandboxed testing** — Run tests in isolated environments
- **Coverage analysis** — Identify untested code paths
- **Performance profiling** — Detect potential bottlenecks

</td>
</tr>
</table>

---

## Features in detail

### 🔍 Code Review
| Feature | Description |
|---------|-------------|
| **Branch diff** | Analyzes all changed files between any two commits |
| **Security scan** | Detects secrets, vulnerabilities, injection risks |
| **Dependency check** | Warns about outdated or vulnerable packages |
| **Style enforcement** | Applies team-defined style guides automatically |

### 🧠 Planning & Triage
| Tool | Description |
|------|-------------|
| `coderabbit review` | Review code changes with JSON or human output |
| `coderabbit plan` | Generate implementation plan from issue/PR |
| `coderabbit triage` | Priority queue of open PRs with risk scores |
| `coderabbit verify` | Sandbox test execution for changes |

### 🛠️ Configurable Analysis
| Config | Description |
|----------|-------------|
| **Languages** | Python, TypeScript, JavaScript, Go, Rust, Java |
| **Tools** | semgrep, eslint, ruff, mypy, bandit, prettier |
| **Profiles** | strict, assertive, conservative, custom |
| **Rules** | Custom rule sets via YAML configuration |

---

## How to use

### Install

```bash
pip install -e .
```

### Quick Start

Review a branch with JSON output (for agents):
```bash
coderabbit review https://github.com/org/repo main --output json
```

Review a local project with human-readable output:
```bash
coderabbit review ./my-project feature-branch --output human
```

Generate an implementation plan from an issue:
```bash
coderabbit plan https://github.com/org/repo/issues/42 --output agent-prompt
```

---

## Agent Integration

Coderabbit speaks the language of AI agents. All commands output structured JSON that your agent can parse directly:

```python
# Hermes or any agent calling coderabbit
import subprocess
import json

result = subprocess.run(
    ["coderabbit", "review", "https://github.com/user/repo", "feature-branch", "--output", "json"],
    capture_output=True, text=True
)

review = json.loads(result.stdout)
print(review["findings"])  # Structured findings ready for agent action
```

---

## Configuration

Create `.coderabbit.yaml` in your repo root:

```yaml
version: 1
language: python
reviews:
  profile: assertive
  auto_review: true

tools:
  semgrep: enabled
  eslint: enabled
  ruff: enabled
  mypy: enabled

knowledge_base:
  guidelines: docs/coding-standards.md

unsafe_symbols:
  - eval(
```

### Configuration Options

| Option | Description |
|--------|-------------|
| `version` | Config schema version (currently 1) |
| `language` | Primary language for analysis |
| `reviews.profile` | strict / assertive / conservative |
| `reviews.auto_review` | Enable automatic review on PRs |
| `tools.*` | Enable/disable specific analysis tools |

---

## Development

### Install dev dependencies
```bash
pip install -e ".[dev]"
```

### Run tests
```bash
pytest tests/
```

### Lint
```bash
ruff check src/
```

### Add new tool
1. Implement the tool interface in `src/coderabbit/tools/`
2. Register it in the tool registry
3. Add configuration option to `.coderabbit.yaml`

---

## Architecture

Coderabbit follows a modular architecture designed for AI agent integration:

```
┌─────────────────────────────────────────────────┐
│                    CLI LAYER                    │
│  ┌─────────┐  ┌─────────┐  ┌─────────────┐       │
│  │ review  │  │  plan   │  │  verify   │       │
│  └────┬────┘  └────┬────┘  └─────┬───────┘       │
└───────┼────────────┼─────────────┼───────────────┘
        │            │             │
        ▼            ▼             ▼
┌─────────────────────────────────────────────────┐
│                   ENGINE LAYER                  │
│  ┌─────────────┐  ┌─────────┐  ┌────────────┐   │
│  │   Analyzer  │  │ Planner │  │ Validator │   │
│  └─────────────┘  └─────────┘  └────────────┘   │
└────────────────────────┬────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────┐
│                    TOOL LAYER                   │
│  ┌───────┐  ┌───────┐  ┌───────┐  ┌───────┐    │
│  │Semgrep│  │ESLint │  │  Ruff │  │  MyPy │    │
│  └───────┘  └───────┘  └───────┘  └───────┘    │
└─────────────────────────────────────────────────┘
```

See [architecture-open.md](./architecture-open.md) for full system design details.

---

## License

MIT License — See [LICENSE](LICENSE) file for details.

---

## Contributing

1. Fork the repo
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## Acknowledgments

- [Semgrep](https://semgrep.dev/) — Static analysis rules
- [Ruff](https://ruff.rs/) — Fast Python linter
- [MyPy](https://mypy-lang.org/) — Python type checker
- [Bandit](https://bandit.readthedocs.io/) — Security linter for Python

<p align="center">
  <strong>Built for AI coding agents everywhere.</strong><br>
  If you're building the next generation of AI software, a ⭐ helps others find it.
</p>