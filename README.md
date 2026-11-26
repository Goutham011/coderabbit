<p align="center">
  <img src="assets/app_icon.svg" width="150" alt="Coderabbit Logo" />
</p>

<h1 align="center">Coderabbit</h1>

<p align="center">
  <strong>Code review for AI agents — CLI-first, offline-capable, extensible.</strong><br>
  A sophisticated code review system that lets your AI coding agent understand context, find issues, and write better code.
</p>

<p align="center">
  <a href="https://github.com/Goutham011/coderabbit/stargazers"><img src="https://img.shields.io/github/stars/Goutham011/coderabbit?style=flat-square&color=gold" alt="GitHub stars" /></a>
  <a href="https://github.com/Goutham011/coderabbit/releases/latest"><img src="https://img.shields.io/github/v/release/Goutham011/coderabbit?style=flat-square&color=blue" alt="Latest release" /></a>
  <img src="https://img.shields.io/badge/platform-Python%203.9%2B-lightgrey?style=flat-square" alt="Python 3.9+" />
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="MIT License" />
</p>

---

## One-Time CLI Integration (Terminal & Desktop Apps)

**Run this ONCE to connect coderabbit to ALL your coding CLIs:**

```bash
cd /Users/gouthamsai/opencode_1/coderabbit
bash setup.sh
```

This adds coderabbit to your shell PATH so it works in:
- **Terminal**: Claude Code, Codex CLI, Cursor terminal, VS Code terminal
- **Desktop Apps**: Claude Desktop, Cursor IDE, GitHub Copilot (via terminal), any desktop app with terminal access

---

## How It Works

When you run `coderabbit review` inside any project directory:

```bash
cd /path/to/your/project
coderabbit review
```

1. **Auto-detects project type** (Android, React, Vue, Python, Go, Rust, etc.)
2. **Genrates configuration** under `.coderabbit/`
3. **Runs native Python deep scan** → finds 100+ issue types
4. **Outputs comprehensive report** with fix suggestions to `.coderabbit/reports/`

---

## Detailed Output: Issues & Fix Suggestions

### What Gets Detected

| Category | Severity | Examples |
|----------|----------|----------|
| **Hardcoded Secrets** | CRITICAL | Keystore passwords, API keys, DB passphrases |
| **Security Vulnerabilities** | HIGH | SQL injection, XSS, code injection (eval/exec) |
| **Release Build Issues** | HIGH | Unsigned APKs, missing ProGuard rules |
| **Architecture Problems** | MEDIUM | Thread-unsafe singletons, memory leaks |
| **AI Slop Patterns** | LOW | Verbose comments, redundant code, over-named variables |
| **Unused Assets** | INFO | Drawables not referenced, dead code |

---

## AI Slop Detection & Removal

Coderabbit identifies and suggests fixes for:

### 1. Redundant Code
**Before:**
```kotlin
private fun isValidUser(): Boolean {
    if (user != null && user.id != null && user.id > 0) {
        return true
    }
    return false
}
```

**Fix:**
```kotlin
private fun isValidUser() = user?.id?.takeIf { it > 0 } != null
```

### 2. Over-Commenting
**Before:**
```python
# This function calculates the sum of two numbers
# It takes two parameters: a and b
# Returns the result as an integer
def add_numbers(a, b):
    return a + b
```

**Fix:**
```python
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b
```

### 3. Verbose Variable Names
**Before:**
```kotlin
val userDatabaseDataSource = UserDataSource(database = database)
```

**Fix:**
```kotlin
val userDb = UserDataSource(database)
```

### 4. Excessive Nesting
**Before:**
```javascript
if (user) {
    if (user.profile) {
        if (user.profile.active) {
            // ... logic here
        }
    }
}
```

**Fix:**
```javascript
if (!user?.profile?.active) return;
// ... logic here
```

---

## Integration with Coding CLIs

### Hermes Agent (Recommended)

Coderabbit is designed to work seamlessly with Hermes Agent. After running `setup.sh`, use in any Hermes session:

```bash
# In your Hermes session, from any project directory:
coderabbit review
# View results in .coderabbit/reports/summary.md
```

**Hermes-specific features:**

1. **Context Memory** - Review results are saved to hermes memory for conversation continuity
2. **Skill Delegation** - Run reviews in separate hermes instance: `hermes -w -q "Review with coderabbit"`
3. **CI/CD Integration** - Auto-fail hermes workflows on CRITICAL issues
4. **Quality Gates** - Block code merges if quality score < 80

**Programmatic usage in Hermes:**

```yaml
# In your .hermes.md or project rules:
coderabbit:
  cli: "coderabbit"
  path: "/Users/gouthamsai/opencode_1/coderabbit"
  config: ".coderabbit.yaml"
```

Then in hermes chat:
```
@review ./path/to/project
@fix hardcoded password in src/Main.kt
@quality report for Agentic_OS
```

### Claude Code CLI
```bash
# After setup.sh, in any project:
coderabbit review
# Use the JSON output to guide Claude's next actions
cat .coderabbit/reports/issues.json | jq '.[] | select(.severity == "HIGH")'
```

### Codex CLI
```bash
# After setup.sh:
coderabbit review
# Codex can read the issues.json and apply the fixes
cat .coderabbit/reports/issues.json > /tmp/codex_context.json
```

### Cursor / Desktop Apps
```bash
# These use your shell/terminal, so once PATH is set:
cd /your/project
coderabbit review
```

---

## Example: Full Analysis of Agentic OS

```bash
$ cd /Users/gouthamsai/opencode_1/Agentic_OS && coderabbit review
[INFO] Project root: /Users/gouthamsai/opencode_1/Agentic_OS
Detected project type: android
Confidence: 8

🔧 Generating configuration...
🔍 Running deep scan...

✅ Scan complete!
   Found 16 issues
   Quality score: 79/100

Report: .coderabbit/reports/summary.md
JSON: .coderabbit/reports/issues.json
```

---

## Fix Commands

```bash
# View detailed fixes
coderabbit fix

# Re-scan after applying fixes
coderabbit review

# Export issues for CI/CD
coderabbit scan /path/to/project --output issues.json
```

---

## Quick Start (Updated)

### 1. One-Time Setup
```bash
cd /Users/gouthamsai/opencode_1/coderabbit
bash setup.sh
source ~/.zshrc  # or open new terminal
```

### 2. Use in Any Project
```bash
cd /path/to/your/project
coderabbit review
cat .coderabbit/reports/summary.md
```

---

## What It Finds

- **CRITICAL** — Hardcoded secrets (keystore passwords, API keys, DB passphrases)
- **HIGH** — Injection risks (SQL, XSS, eval/exec), unsigned release builds
- **MEDIUM** — Architecture issues (threading, memory leaks), verbose code
- **LOW** — AI slop (over-comments, redundant code, long variables)
- **INFO** — Unused assets, dead code paths

---

## Configuration

Create `.coderabbit.yaml` in your repo root:

```yaml
version: 1
language: kotlin
project_type: android

reviews:
  profile: assertive
  ai_slop_detection: true
  code_reduction: true
  unused_analysis: true

analysis_config:
  ai_suggestions: true
  optimization_level: deep
  quality_threshold: 85
  max_line_reduction: 15%
```

---

## Android Build Configuration

### What This Catches

1. **Build Configuration Issues**
   - Missing signing configurations for release builds
   - Incorrect ProGuard rules
   - Gradle secrets in version control

2. **Release-Specific Crashes**
   - Hilt classes stripped by ProGuard
   - Room entities not kept
   - SQLCipher missing native libs

3. **Security & Compliance**
   - Hardcoded keystore passwords
   - API keys in source code
   - Google ToS violations

### Usage

```bash
cd /path/to/your/android/project
coderabbit review
```

The scanner automatically detects Android projects and generates:
- `.coderabbit/coderabbit.yaml` — Android-specific config
- `.coderabbit/rules/android_build.yaml` — Build config rules
- `.coderabbit/rules/android_security.yaml` — Security rules
- `.coderabbit/reports/summary.md` — Findings with fixes

---

## Desktop App Integration

### For Claude Desktop, Cursor, GitHub Copilot Desktop

These apps use your system terminal, so the same `setup.sh` works. After setup:

1. Open your project in the desktop app
2. Open the integrated terminal
3. Run `coderabbit review`

### For App-Specific Terminal Access

If a desktop app has its own terminal environment:

```bash
# Option 1: Add to the app's PATH manually
export PATH="/Users/gouthamsai/opencode_1/coderabbit:$PATH"

# Option 2: Use absolute path
/Users/gouthamsai/opencode_1/coderabbit/coderabbit review
```

---

## Development

```bash
cd /Users/gouthamsai/opencode_1/coderabbit
python3 smart_config.py --help
```

---

## License

MIT License — See [LICENSE](LICENSE) file for details.