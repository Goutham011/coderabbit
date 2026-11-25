# PHASE 5 COMPLETE — Verify Sandbox

**Date:** 2026-11-25  
**Status:** ✅ Done & verified (all tests green, CLI functional)

---

## What was built

### `src/agentic/sandbox.py` (new module, ~237 lines)

**SandboxResult** (dataclass-like):
- Fields: success, command, returncode, stdout, stderr, duration_seconds, artifacts, sandbox_mode
- `to_dict()` → serializable dict
- `to_markdown()` → human-readable report
- `success = (returncode == 0)`

**SandboxManager**:
- `__init__(work_dir=None)` — auto-creates temp dir or accepts custom path
- `_check_docker()` — probes docker availability
- `_build_command(test_type, repo_path, extra_args)` — assembles pytest invocation
  - unit → adds `--cov=. --cov-report=xml --cov-report=term-missing`
  - e2e → adds `--timeout=60`
  - integration → no extra flags
- `run_tests(repo_url, branch, test_type, extra_args, timeout)` — clone + execute + cleanup
- `_clone(repo_url, branch)` — shallow clone to isolated work dir
- `_execute(cmd, timeout, cwd)` — subprocess.run with timeout
- `_limit(text)` — truncates output to MAX_OUTPUT_CHARS with notice
- `_collect_artifacts(out_dir, returncode)` — gathers coverage.xml, screenshots, logs
- `_read_coverage(path)` — parses XML `<line numbers="..." hits="..."/>` into percent
- `_cleanup(path)` / `close()` — safe rmtree with error handling

### CLI additions (`src/agentic/cli.py`)

```bash
agentic verify <REPO> <BRANCH> [--test-type unit|e2e|integration] [--output json|human] [--timeout N]
agentic version                              # v0.5.0
agentic triage [--org FILTER] [--format table|json|md]   # existing
agentic plan --help                          # existing (now imports SandboxResult too)
```

Key decisions:
- Docker fallback: falls back to subprocess when docker unavailable
- Timeout: defaults to 180s, configurable per-invocation
- Coverage parsing: correctly handles comma-separated `numbers` attr by counting each line number individually

---

## Tests added (`tests/test_sandbox.py`, 16 cases)

All passing ✅ (51/51 total)

| Category | Cases |
|----------|-------|
| SandboxResult | default_artifacts, to_dict_keys, success_true, success_false |
| SandboxManager init | work_dir_created, docker_not_available |
| BuildCommand | unit_cov_flags, e2e_timeout_flag, integration_no_extra, extra_args_appended |
| Limit | short_string_unchanged, long_string_truncated |
| CollectArtifacts | missing_coverage_returns_exit_only, read_coverage_parses_valid_xml (80%) |
| Cleanup | removes_path, handles_missing_path |

Coverage: unit mode includes `--cov=. --cov-report=xml --cov-report=term-missing`

---

## Verified

```
$ PYTHONPATH=src python -m pytest tests/ -v
51 passed in 3.98s

$ agentic --version
agentic, version 0.5.0

$ agentic verify --help
Usage: agentic verify [OPTIONS] REPO BRANCH
Options:
  --test-type [unit|e2e|integration]
  -o, --output [json|human]
  --timeout INTEGER               Test timeout in seconds (default: 180)
```

---

## Known limitations

1. No actual Docker containers — currently runs in-process subprocess (falls back gracefully)
2. Network access not isolated (subprocess runs on host network)
3. Resource limits (CPU/memory) not enforced (would need cgroups/Docker for that)
4. Cross-platform subprocess calls assume POSIX-style paths in some places

These are acceptable trade-offs for Phase 5 MVP; Docker isolation is planned for future hardening.

---

## Next phase

**Phase 6:** IDE Plugins (VS Code extension, real-time review during coding)
