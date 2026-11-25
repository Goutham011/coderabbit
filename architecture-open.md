# Agentic Code Review System — Open Architecture

## Philosophy

All features are free. No premium tiers, no paywalled capabilities. The goal is a fully self-hostable, community-driven code review platform where every user gets the same capability. Revenue models (if any) come from hosting/support, not feature gating.

---

## System Components (All Available to Everyone)

### 1. Core Review Pipeline

```
PR Opens → Git Introspection → Analyzer Suite → KGR Update → LLM Contextualize → Comments Posted
                ↓
          Diff + Analyzer Logs + KB Snippets + Custom Rules
```

**Deterministic first, LLM second:**
1. Run SAST/linters in sandbox (Semgrep, ESLint, Pylint, Bandit, etc.)
2. Compute base scores (flaws per 1k lines, severity distribution)
3. Feed results + diff into LLM for human-readable commentary
4. Post threaded comments back to PR

### 2. Tools & Analyzers (Open Stack)

All analyzers run in isolated containers. Self-hosted means you control which tools ship.

**Tier List (No Feature Gates):**
- **SAST**: Semgrep, CodeQL, Bandit, Ruff
- **Linting**: ESLint, Pylint, RuboCop, Go vet
- **Type Checking**: TypeScript checker, mypy
- **Security**: Scancode, dependency audit (pip-audit, npm audit)
- **Format**: black, prettier, gofmt
- **Docs**: markdown lint, docstring checkers
- **Custom**: User-defined rule files via `.agentic/.rules/`

### 3. Knowledge Graph (Persistent Repo Memory)

Per-repo node graph tracking:
- Files ↔ symbols ↔ patterns ↔ issues over time
- Framework/library autodetection
- Historical change patterns (regression detection)
- Code guideline embedding retrieval

**Benefit**: The system remembers your repo across PRs, so reviews reference past decisions, not just current diffs.

### 4. Triage Queue (Cross-Repo Prioritization)

Scoring formula:
```
Priority = (Severity × Weight) + (Urgency × External_Issue) + (Downstream_Blocked × Impact)
```

- P0: Critical security, blocks other PRs
- P1: High severity, time-sensitive  
- P2: Medium, standard flow
- P3: Low, deferred

Attention score per reviewer based on:
- Time since last handoff
- Recent activity level
- Waiting pressure from authors
- Role-based assignments

### 5. Safe Test Execution ("Verify")

Sandboxed behavior validation:
- Clone PR branch in isolated container
- Run synthetic/unit tests
- Record coverage, logs, screenshots
- Return artifacts for human review only

LLM never sees test internals — only the summary.

### 6. Planning Engine ("Plan")

Converts issues/PRDs into implementation plans:
1. Research phase: Query knowledge graph for relevant patterns
2. Design choices: Document alternatives with rationale
3. Phased tasks: Logical chunks with dependencies
4. Agent prompts: Machine-readable instructions for coding agents

Handoff-ready for Claude, Codex, Cursor, Copilot.

### 7. Configuration Schema

`.agentic.yaml`:
```yaml
version: 1
language: python
reviews:
  profile: assertive        # chill / assertive / quiet
  auto_review: true         # always-on or trigger keyword
  path_filters:              # skip certain directories
    - '**/vendor/**'
    - '**/__tests__/**'
tools:
  semgrep: enabled
  eslint: enabled  
  custom_rules:
    - .agentic/rules/security.yaml
knowledge_base:
  guidelines: docs/coding-standards.md
unsafe_symbols:              # blocklist
  - __import__
  - eval(
output:
  inline_comments: true
  summary: frontmatter
```

### 8. IDE & CLI Integration

**CLI Commands:**
```bash
agentic create <repo> <branch>   # Trigger review
agentic verify <repo> <branch>   # Sandbox test
agentic plan <issue-url>         # Generate impl plan
agentic triage                   # View priority queue
agentic token generate           # Auth (not password)
```

**IDE Plugins:**
- VS Code extension
- JetBrains plugin
- Local diff preview

---

## Deployment Options

### Self-Hosted (Recommended for Full Control)

```
Components:
├── Webhook Receiver (GitHub/GitLab/Azure/Bitbucket events)
├── Git Service (clone/fetch/diff generation)
├── Analyzer Runner (containerized tool execution)
├── Knowledge Graph Store (PostgreSQL + vector embeddings)
├── LLM Router (configurable: OpenAI, Anthropic, Ollama, vLLM)
├── Triage Engine (scoring service)
├── Web UI (Next.js dashboard)
└── WebSocket Streamer (real-time updates)
```

### Container Orchestration

Docker Compose or Kubernetes:
```yaml
services:
  webhook:
    image: agentic/webhook:latest
    ports: ["8080"]
  analyzer:
    image: agentic/analyzer:latest
    volumes: ["/tmp/sandbox:/sandbox"]
  llm-router:
    image: agentic/router:latest
    env: [OPENAI_KEY, ANTHROPIC_KEY, OLLAMA_URL]
  postgres:
    image: postgres:16
    volumes: ["/data/pg:/var/lib/postgresql/data"]
  kb:
    image: pgvector/pgvector:pg16
```

### Managed Option (If You Want Hosting)

Not revenue-gated — cost recovery only. Same features, different infrastructure.

---

## Why "Free" Changes the Architecture

| Original CodeRabbit | Our Open Version |
|---|---|
| Flow budgets cap free users | No artificial limits |
| Multi-tenant SaaS pricing | Per-user scaling, not per-feature |
| Enterprise-only deep scan | Everyone gets security scanning |
| Knowledge Base gated | Persistent memory for all |
| Coding Plans Pro-only | Plan engine open |

**Cost implication**: You pay for compute (LLM calls, container runs). But the software itself has no paywall.

**Revenue paths** (optional):
- Hosted version at cost
- Support contracts
- Custom analyzer development
- Consulting/training

---

## Build Order (Phased Approach)

### Phase 1: Core Review (Weeks 1-3)
- GitHub App webhook handler
- Git introspection + diff extraction
- Semgrep + ESLint integration
- Basic LLM prompt for comment generation
- PR comment posting

### Phase 2: Configuration & Knowledge (Weeks 4-6)
- YAML config schema
- File-level knowledge cache
- Pattern detection (frameworks, conventions)
- Auto-review mode

### Phase 3: Triage & Planning (Weeks 7-9)
- Cross-repo PR queue
- Priority scoring algorithm
- Issue-to-plan conversion
- Slack/Teams notifications

### Phase 4: Safety & Sandbox (Weeks 10-12)
- Containerized analyzer isolation
- Verify sandbox
- Unsafe symbol blocking
- Security scoring thresholds

---

## Technology Stack Recommendations

**Backend:**
- Python 3.12+ (FastAPI for webhooks)
- PostgreSQL + pgvector (knowledge graph)
- Redis (task queue, caching)

**LLM Layer:**
- LiteLLM proxy (unified API router)
- Supports: OpenAI, Anthropic, Google, Ollama (local), vLLM (self-hosted)
- Fallback chain: try fast cheap model → escalate to expensive if needed

**Analyzers:**
- Docker containers for each tool
- Resource limits per analysis
- Results aggregated to JSON

**Frontend:**
- Next.js 15 (App Router)
- Tailwind CSS
- tRPC for type-safe API

**Deployment:**
- Docker Compose for single-server
- Helm charts for Kubernetes
- GitHub Actions for CI/CD

---

## Key Design Decisions

1. **No LLM-Only Reliance**: Deterministic tools catch what LLMs miss; LLM explains what tools find.

2. **Graph-Based Memory**: Knowledge persists across sessions. Your repo isn't forgotten.

3. **Configurable, Not Configured-Away**: Users opt-in to features, not locked out.

4. **Open Standards**: YAML config, MCP compatible, provider-agnostic webhooks.

5. **Privacy by Default**: Self-hosted means your code stays yours. Cloud option doesn't train on your data.

---

## Next Steps

Choose starting point:
1. **Prototype Core**: FastAPI + git hook + one analyzer (Semgrep)
2. **Design Data Models**: Schema for commits, PRs, findings, KGR nodes
3. **Write API Contracts**: Webhook events, review pipeline stages, response formats

What would you like to tackle first?
