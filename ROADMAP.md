# Phased Development Roadmap — agentic-cli

## Phase 1: Core CLI (✅ DONE)

**Status:** Working prototype with basic structure.

- [x] CLI skeleton with Click
- [x] Review command (JSON output for agents)
- [x] Token generation
- [x] Config loading from `.agentic.yaml`
- [x] Data models (Finding, ReviewResult, Severity)
- [x] Semgrep integration (placeholder)
- [x] Agent integration examples

**Commands available:**
```bash
agentic review <repo> <branch> --output json
agentic token generate --scope read
agentic plan <source>          # Not implemented yet
agentic verify <repo> <branch> # Not implemented yet
agentic triage                 # Not implemented yet
```

---

## Phase 2: Knowledge Graph (Next)

**Goal:** Persistent repo memory that improves reviews over time.

### Components to build:

1. **Graph Store**
   - Node types: `file`, `symbol`, `commit`, `pattern`, `issue`
   - Edge types: `references`, `imports`, `extends`, `related_to`
   - Storage: SQLite (simple) or Neo4j (scalable)

2. **Indexer**
   - Scan repo on first run + incremental updates
   - Extract symbols (functions, classes, variables)
   - Map file relationships
   - Detect framework patterns (React, Django, FastAPI, etc.)

3. **Query Engine**
   - "Show me all files that use this API"
   - "Find similar patterns to this bug"
   - "What changed in this function over last 10 commits?"

4. **KB Integration**
   - Store coding guidelines as searchable nodes
   - Link findings to relevant guidelines
   - Enable "why this matters" context in reviews

**API:**
```python
from agentic.kb import KnowledgeBase

kb = KnowledgeBase(repo_path="./my-repo")
kb.index()  # Build graph
results = kb.query("find usages of authenticate()")
```

---

## Phase 3: Planning Engine

**Goal:** Convert issues/PRDs into implementation plans handoff-ready for agents.

### Components:

1. **Input Parser**
   - GitHub/GitLab issue URL
   - PRD document (.md, .docx)
   - Free-form description

2. **Research Module**
   - Query knowledge graph for related code
   - Find similar past implementations
   - Identify affected modules

3. **Plan Generator**
   ```
   Summary (2-3 sentences)
   Research findings
   Design choices (with rationale)
   Phases (logical chunks)
   Individual tasks
   Agent prompt (machine-readable)
   ```

4. **Agent Prompt Formatter**
   - Claude Code style
   - Codex style  
   - OpenCode style
   - Hermes style

**CLI:**
```bash
agentic plan https://github.com/user/repo/issues/42 --output agent-prompt
```

---

## Phase 4: Triage Queue

**Goal:** Cross-repo PR prioritization based on value, urgency, impact.

### Scoring Model:

```
Priority Score = 
  (Severity × 10) +
  (External_Urgency × 5) +
  (Downstream_Blocked × 3) +
  (Change_Value × 2) -
  (Review_Effort × 1)
```

### Features:

- Rank open PRs across all repos
- Show "Now" vs "Next" queue
- Attention score per reviewer
- Kanban-style board view

**CLI:**
```bash
agentic triage                    # Default table view
agentic triage --format json      # For automation
agentic triage --org my-org       # Filter by org
```

---

## Phase 5: Verify Sandbox

**Goal:** Safe test execution in isolated environment.
**Status:** ✅ Done — see PHASE5_COMPLETE.md

### Components:

1. **Sandbox Manager**
   - Docker containers for isolation
   - Resource limits (CPU, memory, network)
   - Timeout enforcement

2. **Test Runner**
   - Unit tests
   - E2E tests (browser/emulator)
   - Backend behavior validation

3. **Artifact Collector**
   - Coverage reports
   - Screenshots
   - Logs (scrubbed)
   - Performance metrics

4. **LLM Summarizer**
   - Convert artifacts to human-readable summary
   - Never expose internal details to LLM

**CLI:**
```bash
agentic verify https://github.com/user/repo feature-branch --test-type unit
```

---

## Phase 6: IDE Plugins

**Goal:** Real-time review during coding.

### VS Code Extension (✅ DONE)

See `vscode-extension/` for the full extension.

- ✅ Trigger on save
- ✅ Inline annotations with diagnostics
- ✅ Review panel with webview
- ✅ Keyboard shortcuts (Ctrl+Shift+R, Ctrl+Shift+A)
- ✅ Configurable settings

### JetBrains Plugin

Planned for Phase 6.5:
- IntelliJ IDEA, PyCharm, etc.
- Similar workflow to VS Code

---

## Phase 7: Web UI & Integrations

**Goal:** Dashboard + Slack/MCP integrations.

### Web Dashboard:
- PR queue visualization
- Knowledge base editor
- Custom rules manager
- Team settings

### Integrations:
- GitHub App (native PR comments)
- GitLab MR integration
- Slack bot (notifications)
- MCP server (agent-to-agent)

---

## Current State Summary

| Component | Status | Next |
|-----------|--------|------|
| CLI Skeleton | ✅ Done | Phase 2 |
| Review Command | ✅ Working | Add analyzers |
| Config System | ✅ Working | Add more options |
| Knowledge Graph | ✅ Done | Phase 2 (already complete in v0.5.0) |
| Planning Engine | ✅ Done | Phase 3 (already complete in v0.5.0) |
| Triage Queue | ✅ Done | Phase 4 (already complete in v0.5.0) |
| Verify Sandbox | ✅ Done | Phase 5 (already complete in v0.5.0) |
| IDE Plugins | ✅ Done | Phase 6 - VS Code extension released |
| Web UI | ❌ Not started | Phase 7 |

**Recommended next step:** Phase 7 — Web UI & Integrations (Dashboard, Slack bot, MCP server)
