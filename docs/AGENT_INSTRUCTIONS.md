# Agent Instructions — Code Generation Standards

**Every agent modifying this codebase MUST follow these rules.** Violations are blocking.

---

## Part 1: ASD-STE100 Writing Standard

All documentation, comments, commit messages, and output text MUST follow Simplified Technical English (ASD-STE100) rules:

### Rule 1: One Concept Per Sentence
Use one idea per sentence. Do not join ideas with "and", "or", "but".

```
BAD: The function parses the input and validates it and returns a result.
GOOD: The function parses the input. It validates the input. It returns a result.
```

### Rule 2: Use Active Voice
Subject performs the action. Never use passive constructions.

```
BAD: The file was read by the parser.
GOOD: The parser reads the file.
```

### Rule 3: Use Present Tense
Describe what the code does now. Never use future or conditional speculation.

```
BAD: This will return the value when called.
GOOD: This function returns the value.
```

### Rule 4: Concrete Nouns Only
Name objects precisely. Avoid abstract labels.

```
BAD: Handle the data object.
GOOD: Parse the JSON payload. Return the User record.
```

### Rule 5: Forbidden Words List
Never use these words. Replace with precise alternatives:

| FORBIDDEN | USE INSTEAD |
|-----------|-------------|
| thing | object, value, string, list |
| stuff | data, content |
| handle | process, parse, validate |
| get | retrieve, fetch, obtain |
| make | create, build, generate |
| do | execute, run, perform |
| basically | (omit) |
| really | (omit) |
| very | (omit) |
| quite | (omit) |

### Rule 6: Number Precision
Always include units with measurements. Use numerals for all numbers >= 10.

```
BAD: Run for a long time.
GOOD: Run for 30 seconds.
BAD: There are many entries.
GOOD: There are 42 entries.
```

### Rule 7: No Abbreviations on First Use
Spell out terms before abbreviating.

```
BAD: The API endpoint returned JSON.
GOOD: The application programming interface (API) endpoint returned JSON. The response format is JavaScript Object Notation (JSON).
```

### Rule 8: Imperative Mood for Instructions
Use command form for steps.

```
BAD: You should check the configuration.
GOOD: Check the configuration file.
```

### Rule 9: Maximum 20 Words Per Sentence
If a sentence exceeds 20 words, split it.

```
BAD: This function that was originally designed to parse JSON now also handles XML because we needed backward compatibility.
GOOD: This function parses JSON. It also handles XML. This change enables backward compatibility.
```

### Rule 10: Single Meaning Words Only
One word equals one meaning. Never reuse words with different meanings.

```
BAD: The class runs the runner.
GOOD: The class executes the worker.
```

---

## Part 2: Code Quality Metrics

Track these metrics for every module. Report values in PR descriptions.

### Metric 1: Cyclomatic Complexity (Target: < 10)
Count independent paths through a function.

```python
# Complexity = 1 (simple)
def add(a, b): return a + b

# Complexity = 4 (if/elif/else adds branches)
def classify(x):
    if x > 10:      # +1
        return "high"
    elif x > 5:     # +1
        return "medium"
    else:           # +1
        return "low"
# Total: 1 (base) + 3 (branches) = 4
```

**Rule:** Functions exceeding complexity 10 must be split.

### Metric 2: Lines of Code per Function (Target: < 30)
Count executable lines inside a function body. Exclude blank lines and comments.

```
Target: <= 25 lines per function
Warning: 26-40 lines requires justification
Block: > 40 lines must refactor
```

### Metric 3: Nesting Depth (Target: <= 3)
Count maximum indentation levels.

```python
# Depth = 3 (acceptable)
def process(data):
    if data:              # depth 1
        for item in data: # depth 2
            if item.valid: # depth 3
                yield item
```

**Rule:** Depth > 3 requires extraction into helper function.

### Metric 4: Import Cohesion
Functions in a module must share imported dependencies. No dead imports allowed.

```bash
# Check for unused imports
ruff check --select F401 .
```

### Metric 5: Test Coverage by Module
Minimum coverage targets:

| Module Type | Minimum Coverage |
|-------------|------------------|
| Core logic (models, config) | 90% |
| Engine (review, analysis) | 80% |
| CLI layer | 60% |
| Utilities | 70% |

### Metric 6: File Size Limit
Maximum lines per source file:

```
Source file (.py): <= 200 lines
Test file: <= 300 lines
Configuration: unlimited
Documentation: unlimited
```

Files exceeding limits must be split by responsibility.

### Metric 7: Public API Surface
Count public functions/classes exposed per module.

```
Target: <= 5 public symbols per module
If > 5: Split into submodules
```

### Metric 8: Dependencies per Module
External packages used per module.

```
Core modules: <= 3 external deps
CLI modules: <= 5 external deps
Tools/integrations: <= 8 external deps
```

Justify any exception in docstring.

### Metric 9: Duplicate Code Detection
Identical or near-identical blocks across files are forbidden.

```bash
# Detect duplication
radon clone .
```

**Rule:** Any duplicated block > 5 lines must extract to shared function.

### Metric 10: Error Handling Completeness
Every I/O operation, network call, and subprocess invocation must handle errors.

Checklist:
- [ ] Network calls have timeout
- [ ] File operations catch FileNotFoundError
- [ ] JSON parsing catches JSONDecodeError
- [ ] Subprocess calls catch TimeoutExpired
- [ ] All exceptions preserve context

---

## Part 3: Implementation Rules

### Rule 11: Minimal Implementation
Write the fewest necessary lines to achieve correctness. Remove everything else.

```
Before refactoring:
  - Are there unused variables? Delete them.
  - Are there redundant checks? Remove them.
  - Can two functions merge? Merge them.
  - Is a class just grouping functions? Make it a module-level function.
```

### Rule 12: No Redundant Abstractions
Do not create interfaces, base classes, or abstractions without a second concrete implementation.

```
BAD: Create AbstractAnalyzerBase for future analyzers
GOOD: Create SemgrepAnalyzer. When ESLintAnalyzer arrives, extract common pattern.
```

### Rule 13: Single Responsibility per File
Each file implements one capability. If a file grows beyond 200 lines, split by responsibility.

File purpose examples:
- `models.py` — Data structures only
- `config.py` — Configuration loading only
- `review.py` — Analysis orchestration only
- `cli.py` — Command definition only

### Rule 14: Explicit Over Implicit
Never rely on hidden behavior. Make all dependencies visible.

```
BAD: from . import *  (hides what is imported)
GOOD: from .models import Finding, ReviewResult  (explicit)
```

### Rule 15: Fail Fast, Fail Loud
Invalid inputs must raise immediately with clear error messages. Never proceed with bad state.

```python
# Good
def analyze(diff: str) -> list[Finding]:
    if not diff:
        raise ValueError("Diff cannot be empty")
    ...
```

### Rule 16: Constants for Magic Values
Extract unexplained literals to named constants.

```
BAD: if severity == "c":  # What does c mean?
GOOD: if severity == Severity.CRITICAL.value:  # Clear intent
```

### Rule 17: Type Annotations Required
Every public function must declare parameter and return types.

```python
# Required
def review(repo: str, branch: str) -> ReviewResult: ...

# Not required (private helpers with obvious types)
def _helper(x): ...
```

### Rule 18: Docstrings for Public APIs Only
Private functions (_prefix) need no docstring. Public functions require one-line summary.

```python
def calculate_score(findings: list[Finding]) -> float:
    """Calculate confidence score from findings."""
    ...
```

---

## Part 4: Security Rules

### Rule 19: No Hardcoded Secrets
Scan for secrets before committing.

```bash
# Check before push
gitleaks detect --report-format json
```

Forbidden patterns:
- API keys in source code
- Passwords in configuration
- Private tokens in examples
- Secret strings in commits

### Rule 20: Input Validation at Boundaries
Validate all external input: CLI arguments, file paths, URLs, subprocess output.

```python
# Validate paths
path = Path(user_input).resolve()
if not str(path).startswith(str(base_dir)):
    raise ValueError("Path traversal detected")
```

### Rule 21: Secure Defaults
Security-sensitive settings default to restrictive mode.

```python
class Config(BaseModel):
    auto_review: bool = False  # Disabled by default
    allow_network: bool = False  # Disabled by default
```

---

## Part 5: Testing Rules

### Rule 22: Tests Mirror Production Code Standards
Same ASD-STE100, same quality metrics, same security rules apply to test files.

### Rule 23: Each Test Validates One Behavior
One assertion per test where possible. Named to describe the behavior.

```python
def test_empty_diff_returns_no_findings():
    ...
    
def test_critical_finding_sets_exit_code_to_two():
    ...
```

### Rule 24: No Mocked Production Logic
Tests must exercise real code paths. Mock only external systems (network, filesystem).

---

## Part 6: Documentation Rules

### Rule 25: README Documents Usage, Not Implementation
The README answers: What does this tool do? How do I run it? What output does it produce?

### Rule 26: Commit Messages Follow Conventional Format
```
<type>(<scope>): <subject>

<body>  # Optional but required for breaking changes
<footer>  # Required for breaking changes or deprecations
```

Types: feat, fix, docs, style, refactor, test, chore

### Rule 27: AGENTS.md Is the Source of Truth
When in doubt about coding standards, read this file. Conflicts resolve to this document.

---

## Quick Reference Checklist

Before submitting any change, verify:

- [ ] Code follows ASD-STE100 (no forbidden words, active voice, present tense)
- [ ] Cyclomatic complexity < 10 for all functions
- [ ] No function exceeds 30 lines
- [ ] Nesting depth <= 3
- [ ] No unused imports
- [ ] All public functions have type annotations
- [ ] All public functions have one-line docstring
- [ ] Test coverage meets module targets
- [ ] No hardcoded secrets
- [ ] External inputs validated
- [ ] Error handling covers all I/O operations
- [ ] File size <= 200 lines
- [ ] No duplicate code blocks > 5 lines

**If any box is unchecked, the change is incomplete.**
