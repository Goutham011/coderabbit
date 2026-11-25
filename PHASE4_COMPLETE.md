# Phase 4 — Triage Queue
**Status:** Complete  
**Version:** 0.4.0

## Scope
Cross-repo PR prioritization using the weighted scoring formula from the pipeline spec:

```
Priority Score = (Severity × 10) + (External_Urgency × 5) + (Downstream_Blocked × 3)
               + (Change_Value × 2) - (Review_Effort × 1)
```

Queue buckets: **Now** (≥15), **Next** (≥8), **Later** (<8).

## Files added / changed

| File | Action |
|------|--------|
| `src/agentic/triage.py` | New — `PRItem`, `TriageQueue`, `ReviewerScore` |
| `src/agentic/cli.py` | Updated — `triage` command with table/json/md output |
| `src/agentic/__init__.py` | Updated — exports triage classes, bumps to v0.4.0 |
| `tests/test_triage.py` | New — 18 tests covering scoring, sorting, filtering, serialization |
| `PHASE4_COMPLETE.md` | This file |

## CLI usage

```bash
# Default table view
agentic triage

# JSON for automation pipelines
agentic triage --format json

# Markdown for issue trackers or docs
agentic triage --format md

# Filter by organization
agentic triage --org acme
```

## Sample output (table)

```
# Triage Queue

Total PRs: 5

## Now (urgent)

| # | Repo | PR | Title | Author | Score |
|---|------|----|-------|--------|-------|
| 2 | acme/core | #42 | Fix auth bypass vulnerability | alice | 38.0 |
| 1 | acme/data | #203 | Fix data migration race condit | dave | 30.0 |

## Next (standard)

| # | Repo | PR | Title | Author | Score |
|---|------|----|-------|--------|-------|
| 1 | acme/api | #87 | Add rate limiting to endpoints | bob | 12.0 |

## Later (routine)

| # | Repo | PR | Title | Score |
|---|------|----|-------|-------|
| 2 | acme/web | #15 | Update dependencies | 6.0 |
| 1 | acme/auth | #11 | Refactor token validation | 4.0 |
```

## Test results
35 passed, 0 failed. All triage-specific tests (18) green.

## Future work
- Connect triage to live GitHub API (`agentic login` tokens already stored)
- Fetch real PR state (labels, assignees, branch protection blocks)
- Render reviewer attention scores alongside the queue
- Persist queue state to disk for multi-session tracking
