# Project Structure — agentic-cli

```
coderabbit/
├── src/
│   └── agentic/
│       ├── __init__.py      # Package exports
│       ├── __main__.py      # CLI entry point
│       ├── cli.py           # Click-based CLI commands
│       ├── review.py        # Review engine (analyzers + LLM)
│       ├── config.py        # Configuration management
│       └── models.py        # Pydantic data models
├── tests/
│   ├── __init__.py
│   └── test_review.py       # Unit tests
├── examples/
│   └── agent-integration.py # How agents can use this CLI
├── .agentic/
│   └── rules/               # Custom Semgrep rules
│       └── custom.yaml
├── example.agentic.yaml     # Example configuration
├── pyproject.toml           # Python package config
└── README.md                # Documentation
```

## Key Files

| File | Purpose |
|------|---------|
| `src/agentic/cli.py` | Main CLI with click — all commands defined here |
| `src/agentic/review.py` | ReviewEngine class — orchestrates analysis pipeline |
| `src/agentic/models.py` | Data models: Finding, ReviewResult, Severity |
| `src/agentic/config.py` | Config loading from .agentic.yaml |
| `examples/agent-integration.py` | Code examples for Hermes, Claude Code, Codex, etc. |

## Agent Integration Points

Any coding agent can call agentic via subprocess:

```bash
# JSON output — easy to parse
agentic review <repo> <branch> --output json

# Human-readable output
agentic review <repo> <branch> --output human
```

The JSON output is designed for machine consumption:
- `overall_severity`: "critical" | "high" | "medium" | "low" | "info"
- `findings`: Array of structured findings with rule, message, file, line
- `confidence`: Float 0-1 indicating analysis certainty
- Exit codes: 0 = pass, 1 = warning, 2 = critical blocking

## Next Steps

1. **Phase 2**: Add Knowledge Graph (persistent repo memory)
2. **Phase 3**: Add Planning engine (issue → implementation plan)
3. **Phase 4**: Add Triage queue (cross-repo PR prioritization)
4. **Phase 5**: Add Verify sandbox (isolated test execution)
5. **Phase 6**: IDE plugins (VS Code, JetBrains)
6. **Phase 7**: Web UI dashboard
