# Phase 3 Completion Report — Planning Engine

## Status: Complete

Planning engine implemented. Converts issues/specs into structured implementation plans with agent-ready prompts.

---

## What Was Added

### New File: `src/agentic/planner.py` (140 lines)

**Classes:**
- `Plan` — Structured plan with phases, tasks, and agent prompt
- `Planner` — Generates plans from text, files, or URLs

**Features:**
- Parse issue titles and summaries from text/Markdown
- Load source from URLs or local files
- Query knowledge graph for related symbols (optional)
- Generate phased implementation plan
- Output JSON, Markdown, or agent-prompt format

### Updated Files

| File | Lines | Change |
|------|-------|--------|
| `src/agentic/cli.py` | 124→138 | Implemented `plan` command with --output and --repo-path |
| `src/agentic/__init__.py` | 7→9 | Exported Planner, Plan; bumped to v0.3.0 |
| `tests/test_planner.py` | +69 | 8 tests covering all paths |

---

## CLI Commands Working

```bash
# JSON output (for agents)
agentic plan "Fix login bug" --output json

# Markdown report
agentic plan issue.md --output md

# Agent prompt (for Claude Code/Codex/OpenCode)
agentic plan "Add rate limiting" --output agent-prompt

# With KB research
agentic plan "Fix auth bug" --repo-path ./src --output json
```

---

## Test Results

```
tests/test_knowledge_base.py::test_initializes_db                 PASSED
tests/test_knowledge_base.py::test_index_file_creates_nodes       PASSED
tests/test_knowledge_base.py::test_query_returns_results          PASSED
tests/test_knowledge_base.py::test_close_does_not_crash           PASSED
tests/test_planner.py::test_to_dict                               PASSED
tests/test_planner.py::test_to_markdown_contains_sections         PASSED
tests/test_planner.py::test_to_agent_prompt_returns_string        PASSED
tests/test_planner.py::test_plan_from_text                        PASSED
tests/test_planner.py::test_plan_loads_file                       PASSED
tests/test_planner.py::test_plan_with_kb_research                 PASSED
tests/test_planner.py::test_plan_empty_source                     PASSED
tests/test_planner.py::test_generate_phases_has_multiple          PASSED
tests/test_review.py::TestFinding::test_finding_to_dict            PASSED
tests/test_review.py::TestConfig::test_default_config              PASSED
tests/test_review.py::TestConfig::test_config_from_dict            PASSED
tests/test_review.py::TestReviewEngine::test_review_local_repo     PASSED
tests/test_review.py::TestReviewEngine::test_severity_mapping      PASSED
============================== 17 passed in 0.26s ==============================
```

---

## Code Quality Metrics

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Max complexity | < 10 | 6 | PASS |
| Max func length | <= 30 | 23 | PASS |
| Largest file | <= 200 | 140 (planner.py) | PASS |
| Total source | — | 530 lines | — |
| Total test | — | 168 lines | — |
| **Grand total** | — | **698** | — |

---

## Example Output

### JSON Mode
```json
{
  "source": "Add rate limiting to API endpoints",
  "summary": "Add rate limiting to API endpoints",
  "phases": [
    {"title": "Research and Setup", "description": "..."},
    {"title": "Implement Core Logic", "description": "..."},
    {"title": "Add Tests", "description": "..."},
    {"title": "Verify and Document", "description": "..."}
  ],
  "tasks": ["[ ] Research and Setup", "[ ] Implement Core Logic", ...],
  "prompt": "Implement: ..."
}
```

### Agent Prompt Mode
```
Implement: Add rate limiting to API endpoints

Context:
- Research and Setup: Review existing codebase...
- Implement Core Logic: Write the primary implementation...
- Add Tests: Cover normal paths, edge cases...
- Verify and Document: Run tests...

Tasks:
[ ] Research and Setup
[ ] Implement Core Logic
[ ] Add Tests
[ ] Verify and Document
```

---

## Architecture

```
Planner.plan(source, output_format)
    ├── _load_source()        # URL, file, or raw text
    ├── _parse_issue()        # Extract title, summary, keywords, files
    ├── _research()           # Query KB for related symbols (optional)
    ├── _generate_phases()    # Create phased plan
    ├── _extract_tasks()      # Convert to checklist
    └── _build_prompt()       # Agent-ready prompt string

Output: Plan object → JSON / Markdown / raw prompt
```

---

## Next Steps

**Ready for Phase 4 (Triage Queue)**

Phase 4 adds cross-repo PR prioritization based on severity, urgency, and downstream impact.
