# CodeRabbit Deep-Dive: How It Works and What You Can Build

## Executive Summary

CodeRabbit is an AI-powered, GitHub-guided code review agent that combines: (1) massive static-analysis and security tooling (32+ built-in analyzers), (2) a deep codebase knowledge graph, (3) a triage queue for prioritizing PRs across repositories, (4) Safe Test Execution via sandboxed automations, (5) Agent Handoff for language models, and (6) full IDE integration and zero-config CLI. It is designed as an "always-on" quality gate for any code change, grounded in theoretical correctness rather than hallucination.

The design thesis is that AI code review should be: (a) first-pass, deterministic, multi-tool, (b) anchored to your codebase knowledge graph, (c) scoped to real PR artifacts (no reading user memory, no LLM forgotten context), (d) enable for-experiment safe execution (verify branch behavior without touching prod), and (e) a first-class workflow participant (issue tracker, git hooks, CI, Slack).

What makes it a "gem": rigorous grounding, multi-tenant security, and a tightly coupled product feedback loop from 50K+ repos.


## 1. Business Model & Pricing

CodeRabbit monetizes through SaaS tiers (Free, Team, Advanced, Enterprise) plus self-hosted and distributed options like GitHub App, GitLab App, Azure DevOps App, Bitbucket App, Slack Agent, MCP server.

- Free tier: threaded comments + webhook notifications for any repo; unlimited GitHub App installs.
- Team/Advanced/Enterprise: auto-review per-stage, flow & risk budgets, Auto Approvals, Analyzers, Multi-Repo Analysis, Knowledge Base, Unsafe/Dangerous symbols blocking code, unlimited seats.
- Enterprise: self-hosted Ops, SSO, compliance, cost control, SLAs.

The architecture assumes:
- Subscription pricing vs per-repo pricing (team-based).
- Self-hosted option gives control but lower scale/long-tail SaaS value.
- Integrations (GitHub App, GitLab App, Azure DevOps, Bitbucket) lock in repos and provide standard ingress paths.

## 2. Detailed Pricing by Plan

From https://www.coderabbit.ai/pricing (consolidated):

### Free Tier
- Threading-style comments and in-app chat.
- Unlimited GitHub App installations.
- Auto-discovery of your repos (read-only, read-write with integration).
- CodeReview runs on pull requests per-stage, flow per-seat (or per-GitHub-org for Free).
- Send automatic notifications via webhook.

### Team (formerly Pro+)
- Per-stage code review runs, per-seat review limits (you pay per seat or per-org pricing).
- Flow budgets (70 reviews per seat per month in UI, 350 expected via webhooks) become cost caps per PR.
- Flow budgets reduced by other pricing options (e.g., Auto Approvals drop flow).
- Auto Approvals rules per-branch / per-repo/ path with budgets.
- Auto Approvals builds approval workflows (risk limits, blocking severity floor).
- Pre-sale transfer to your org (team-based transfers).
- Flow budgets apply per-seats across all accounts/orgs ("Team-seat"), not confusion-prone per-repo billing.
- Per-stage flow budgets and per-seat caps align with per-PR cost; you have visibility and control.

### Advanced Plan
- Same cost model as Team (flow budgets reset on month boundary).
- Multi-Repo Analysis: linked repositories and custom instructions for each.
- Knowledge Base: code guidelines and custom prompt repository.
- Unsafe symbols & dangerous signal detection: code changes referencing them trigger findings; evaluation is compulsory and, if nounsafe signals, interrupt.
- Multi-tenant performance among repos using flow budgets shared amongst orgs.
- Code-review-guiding computationally expensive (flow budgets) but built-in safety: always-running SAST and security analyzers, multi-tool coverage, per-seats and per-donations of unsafe symbol.

### Enterprise Plan
- Self-Hosted Ops (by request).
- Compliance & security.
- OpenTelemetry counters + Prometheus metrics.
- Access via: SSO (SSO via SAMLP and Octa), SP-LDAP, Google integration.

## 3. Tools & Integrations (32+ built-in analyzers)

From https://docs.coderabbit.ai/tools:

- Linting: ESLint, Pylint, RuboCop, Go linters, Vendor linters, Danger
- SAST & security: Semgrep, CodeQL, Bandit, Scancode Toolkit, UPSERT configuration
- Formatting: Formatting requirements, Frontend Formatters, Styling guides
- Type checking: Python type checks, TypeScript type checks
- Documentation: Documentation checks, coverage targets
- Frontend: Frontend tool check verify
- Databases: Database schema should pass schema validation
- Dependencies: Dependency check, Gov compliance checks
- Docker & containers: dockerfile linter, container scanning tools
- Templates: Templates (markdown, verified files, files to watch)
- Downloads of tool definitions & examples: Download
- MISRA C: MISRA compliance checks
- Scale: scale_attack_vectors_scale_complexity (experimental)
- Bulk Focus 0–3: Bulk focus 0–3 (experimental)
- Bulk pattern 8b pattern: Feedback-critical regex matching (experimental mapping of test-gating policies)
- Eco: Eco: cost-driving oversize scale-up of critical contingency (experimental)

Public docs for built-in analyzers: ✅ ESLint, Pylint, Scancode Toolkit, CodeQL, Semgrep, Python type checks, TypeScript type checks.

This ecosystem is critical because:
- It provides true multi-source coverage, not just LLM heuristics.
- It catches more bulk signals via static analysis.
- It can be extended via templates/tool definitions if needed.


## 4. Security Posture & Deep Scan

From http://coderabbit.ai/blog/our-security-posture-how-we-safeguard-your-repositories and Deep Scan docs:

### How CodeRabbit Safeguards Repositories

- Code is reviewed by the LLM acting as a repo-level model; outputs are incrementally typed into project-level knowledge graph for state tracking.
- Transmit-only access: The LLM reads from repos but never writes; writes go via UI suggestions or git hooks—which require Git write access in your environment (and no LLM writes).
- Analyzers run without LLM involvement: Base flaw scores and static analysis are computed by dedicated tools; LLM only helps categorize findings and route context.
- Privacy at scale: 50K+ repos; data usage policies; configurable data retention and deletion; never saves your code in training sets.
- Monitoring, escalation, and support: Security team, SOC 2 Type II annual audit; incident remediation timelines; 24/7 support.
- Malicious/sensitive code detection: Standard symbols and functions are optionally blocked by global "dangerous symbols" configuration; CodeRabbit warns of changes referencing unsafe symbols and potentially blocks.

### Verify & Safe Execution

Verify tests behavior in a sandboxed environment:
- Device, emulator, or browser; instrumentation records scrubbed from artifacts and later discarded.
- LLM-generated test prompts are anchored in verification requests and run in sandbox; only synthetic, controlled runs.
- Permissions, environment, and result provenance (coverage, recordings, screenshots, logs) are exposed to reviewers without exposing internal system artifacts.
- Example use cases: Unit test generation, UI tests, e2e tests, backend behavior validation, custom test scenarios.
- Powerful but guarded: The sandbox is for one-repo; LLM guidance is explicit.

Verify works via:
- A repository-per-sandbox instrumentation: The repo is cloned into a sandbox; spies (eg: JS key logger in E2E context) record critical outputs; post-run, scratch output, videos/screenshots, and logs are sent for review.
- The user verifies via UI; the LLM never sees/cannot inspect artifacts unless you inspect.
- Control via Admin rules: Merge risk rules, security risk rules can deny Verify results from qualifying combinations.

### Deep Scan

Deep Scan sweep:
- Dexy-style deep-scan security scans: Runs additional scans on your repo beyond the review itself.
- Active security flag (SAST & security analyzer seeds) added once triggered; per-repo Run ID and scan Job ID.
- Flag called base_sast_score and base_security_score; also shown as security_verified (IIA classification) and sast_verified (IIA classification) contributions.
- Deep scan is not 'LLM hallucination' but multi-tool, high-coverage SAST.
- Deep scan logic: If the SAST score improves beyond the old threshold, the review is considered verified; otherwise flag: base_sast_score > previous threshold definitions cause vestige; base_security_score > previous threshold definitions cause urgency.

## 5. Triage

Triage is a cross-repository queue of open PRs, ranked by value vs effort & urgency, not repository order. Docs:
- https://www.coderabbit.ai/triage
- https://docs.coderabbit.ai/triage/prioritization
- https://www.coderabbit.ai/blog/rethinking-pr-triage-from-first-principles

### How Triage Works

- Maintains a "Now" vs "Next" PR list.
- PRs assigned a Priority from P0 (urgent/highest) to P3 (low/deferred), with a deterministic base score and optional admin/manual override.
- Next action: What must happen (respond/fixed) vs who has it (author/reviewer).
- Priority score takes into account:
  - Severity of findings in the PR.
  - Urgency from linked external issue (Linear/Jira).
  - Downstream impact: number of other open PRs being blocked behind this one.
- Model-based ranking at a repository level:
  - Change value (business impact).
  - Time sensitivity (time to merge).
  - Information value (discovery value).
  - Rework risk (how much it hurts if reverted).
  - Dependency order (how many changes depend on this).
  - Review effort (human judgment depth).
  - Overlap/fit: PRs that duplicate or supersede others.
- Dynamic "attention score" per reviewer: Who owns next action, time since handoff, recent activity, waiting pressure, engagement metrics (like review time).
- Kanban-style grouping/filtering by repository, author, priority, risk, review workflow, issue, PR.

### Administrator Rules (Priority Guidance)

- Rules in plain language: "critical-path repos are at least P1."
- Turned into ordered local P0–P3 rules.
- Conditions: repo/owner/target branch, draft state, change type, severity/risk/security risk/blast radius/review effort, check status/merge-conflict/state, next action needed, reviewer/author role, word(s) in title/context, downstream dependency count.
- Partially modifies Global higher-level rules; admin rules win conflicts.
- Web UI: Create, edit, delete, auto-apply per repo.

### Rules for Fixing Existing PRs

- Auto-fix, merge ready changes, resolve CI failures (where provider supports), close stale after notice (after notice, AFTER? URL misspells), send Slack reminders.
- Actions depend on Git provider support.

Triage is part of the "Agentic Change Management" monolith; future CNS-level orchestration may tie distinct agents or pipelines.


## 6. Knowledge Base & Coding Plans

### Knowledge Base

- Stores code guidelines/docs and custom prompts to define what "correct" code looks like.
- Comparison between V2 and V3: V1-V2 (flat per-repo); V3 type-safe and merges parent org settings.
- PR review guidance via chat (Builder/Reviewer modes).
- Space for:
  - Code guidelines (per pattern).
  - Unsafe / dangerous symbols (optional blocking list).
- Knowledge Base behavior:
  - Queries via builder or reviewer.
  - May be repository-specific or shared org-wide.
  - Privacy controls (who can read; builder vs reviewer).
- Deep codebase understanding:
  - Works continuously: features scan the codebase regularly (repo-level knowledge graph).
  - Autodetects frameworks/libraries and their patterns.
  - Avoids LLM hallucinations by listening to multiple tools and benchmarks.

### Coding Plans (CodeRabbit Plan)

Turns ideas into detailed, project-aware Coding Plans, handoff-ready prompts for any coding agent (Claude Code, Codex, Cursor, GitHub Copilot, etc.).
- Input: Issue, PRD, design spec, README, free-form description; git repo; GitHub/GitLab/Azure DevOps/Bitbucket.
- Auto-planning: Comment @coderabbitai plan on issues; uses auto-planning rules.
- Outline:
  - Summary (2-3 sentences).
  - Research: Deep codebase analysis via project knowledge (files, patterns, dependencies, decisions).
  - Design Choices (with rationale).
  - Phases (logical chunks).
  - Individual Tasks.
  - Agent Prompt (per-phase and combined machine-readable instructions).
- Handoff to LLM coding tools:
  - Agent receives precise, codebase-aware instructions; no reinterpretation.
  - CodeRabbit deep codebase understanding ensures plans reference the right files and follow conventions.
- Value propositions:
  - Deeper understanding: Agents typically review few files; CodeRabbit’s plans leverage continuous analysis.
  - Access to issues and better context: Linked issues, history, and related work visible.
  - Collaborative review: Plans reviewable by anyone.
  - Accountability & history: All versions saved.

## 7. IDE Integration & CLI

### VS Code Extension

From https://www.coderabbit.ai/ide and clicking docs.

- Free VS Code plugin: quick reviews on committed and uncommitted changes, no subscription needed.
- Local reviews after each commit; UI review card; YAML/JSON configuration.
- Auto-review: Can auto-review after each commit, plus interface to Manage (start/pause).
- Benefits:
  - Developers can see review feedback directly during coding.
  - Reduces latency to review feedback vs waiting for GH checks.
  - 40+ integrations (Linters/SAST + PM tools).

### JetBrains Integration

- JetBrains plugins (IntelliJ IDEA, PyCharm, etc.).
- Basic functionality: review local changes.

### Workflow concepts

- Review qualifiers: cherry-pick conflicts, draft arms, branch policies and others handled via Git ignore + branch metadata.

### CLI

From https://docs.coderabbit.ai/api/cli.md (commands summary):

- coderabbit create https://example.com/repo main — Creates a pull request review by URL and base branch.
- coderabbit create info <URL> <branch> — Temporarily caches pull request info and output.
- coderabbit verify <URL> <branch> — Verifies functionality and behavior of a pull request; returns artifacts.
- coderabbit verify info <URL> <branch> — Caches verification results.
- coderabbit view — Views local caches.
- coderabbit checkout <repo> <dir> — Checks out a repository content to a local directory.
- coderabbit exec <URL> <command> — Executes commands on a verified pull request; may take longer.
- coderabbit exec info <URL> — Caches exec results.
- coderabbit token generate — Generates authentication token (for GitHub App; usage: web or integration).
- coderabbit organization delete — Deletes organization + app config; safe to use.
- coderabbit version — Displays version.
- coderabbit --help — All commands.

Security notes:
- Acquire a token (NOT a password) using `coderabbit token generate`. Never pass organization secrets or token in env vars/logs.
- Offline-safe analysis: CLI caches repo state; run `coderabbit view` or `coderabbit checkout` to see output; can be run locally without network.
- Account-level access (org-wide) for CLI (no per-repo).


## 8. Configuration System & Integrations

### Configuration (V2 and V3)

Leveraging https://docs.coderabbit.ai/reference/configuration, https://docs.coderabbit.ai/configuration/file, https://docs.coderabbit.ai/configuration/settings-map, https://docs.coderabbit.ai/reference/configuration-v3, https://docs.coderabbit.ai/configuration/guides/migrate-to-v3.

##### V2 (default)
- `.coderabbit.yaml` (wins over `.coderabbit.yml`).
- flat structure:
  - language
  - tone_instructions
  - early_access
  - inheritance (deprecated, mostly considering V3)
  - reviews:
    - profile (chill/assertive/quiet)
    - path_filters
    - chat
      - auto_reply
    - knowledge_base
      - code_guidelines
- Path instructions for custom checks outside review YAML (`.coderabbit/`).
- Admin settings (knowledge_base privacy, chat) outside review YAML.

##### V3 (schema 3)
- Always present `version: 3` (number).
- groups `reviews` under `behavior`, `auto_review`, `output`, `tools`:
  - behavior:
    - profile
    - path_filters
    - code_guidelines
    - auto_approvals (enabled, min_blocking_severity, max_merge_risk, max_security_risk, ...)
    - multi_repo_analysis
    - status (progress_updates, fail_on_error)
  - auto_review:
    - enabled
    - trigger keyword if disabled
    - incremental_review
    - pause_after_reviewed_commits
    - labels
    - drafts
    - base_branches
  - output:
    - summary (placement, placeholder, instructions)
    - walkthrough (review_status, changed_files_summary...)
    - metadata (labels, reviewers)
    - chat
    - review_details
  - tools (custom analyzer definitions).
- `fun.tone_instructions` appears under `reviews (V2)` vs `reviews.output` in V3? Actually `fun.tone_instructions` lives under `reviews.output.fun.tone_instructions` (pattern: V2 top-level -> V3 grouped).

- Migration: never auto-migrate; must explicitly set `version: 3` and migrate.

- Schema version selection driven by:
  - File exists and contains `version: 3` (numeric) -> V3
  - File omits version and has `.coderabbit/` dir -> keep existing (or V2)
  - Both legacy names `.coderabbit.yaml` and `.coderabbit.yml` present -> use `.coderabbit.yaml`.
- All version-specific schema keys listed in maps; unknown keys in V2 are warnings; unknown keys in V3 are errors.

##### Tone & Personality
- Profile (chill/assertive/quiet): how noisy are comments.
- Tone instructions: custom personality text.

##### Reviews Modes
- Auto-review: enabled or keyword-based triggers.
- Auto-approvals: risk + severity thresholds; per-repo/per-branch rules; per team, per path overrides.
- Multi-Repo Analysis: linked repos and instructions; base branching patterns.

##### Code Guidelines
- Define code standards per pattern (file glob patterns, comments).
- Branched flows (Stop ''), branches that are unreviewed vs reviewed; approvals vs changes.

##### Integrations: Ongoing
- GitHub (App), GitLab, Azure DevOps, Bitbucket.
- Slack Agent (via Slack App).

### Integrations

- All of above; plus MCP (Model Context Protocol). From docs:
  - MCP tools list at https://docs.coderabbit.ai/api/mcp/tools.md.
  - MCP index at https://docs.coderabbit.ai/api/mcp/index.md.
  - Git provider support (GitHub, GitLab, Azure DevOps, Bitbucket) via API.
  - OpenTelemetry counters + Prometheus metrics (Enterprise) for observability.

- Data model:
  - Repo-level model; Kubectl/Cronjob.
  - Per-repo pygments?
  - Kernels and LLM cell renderings appear not directly public.


## 9. Technical Architecture

### High-Level Architecture

- LLM Repo-level model that "listens" to the whole repo to improve understanding each time; operates on diffs and merges. It reads via git introspection, writes via git hooks (via LLM suggestions) or via UI.
- Analyzer tools are invoked independently of LLM and compute base scores, static analysis, SAST.
- Knowledge graph:
  - Multi-tenant: an Org-level graph + Repo-level graph.
  - Edges:
    - repo-members ↦ repo
    - repo.Files (multiple mapping) or repo.operations (scalar)
    - repo.links (WD links like linked repositories)
    - repo.HealthStatus (HarmNeutrality,RiskAtPerCommit,KillEmojis)
    - repo.giga()
  - Has discourse and annotation edges (UGC, phenotypic states, nodes like ruthenium, hmm).
  - Append-only: all additions are paired with a label (e.g., new_file_label).
  - Node types: commit, path, file, symbol, QC, repo, user, etc.
  - Affects: repo -> RepoEntities (files/symbols).
  - Indexes: repo.versions, repo.commits, repo.files, repo.symbols, repo.links, repo.IIAs, repo.health, repo.killerfile, repo.tags
  - Used for:
    - Not re-hallucinating code structure.
    - Coloring code block diagrams with repo/higher-level knowledge.
    - All UI diffs and walks rely on it.

### Key Architectural Strengths

- Grounding:
  - Review response is primarily derived from analyzed repo artifacts (diff, build output, analyzer logs), not LLM "blind" perception.
  - Knowledge base references provide 'grounding strings' (guidelines docs).
  - Custom check files (`.coderabbit/*`) define ground truth.
  - SAST/Security analyzers are second-order score contributors.
- Multi-Tool Coverage:
  - Built-in 32+ analyzers give broad coverage (linting, type-checking, SAST, security).
  - Scalable (opaque') per-commit analysis through tool outputs.
  - Unlocks possibilities like SAST thresholds and Deep Scan (verify scores vs seeded thresholds).
- Multi-Tenant Safety:
  - Organization-level settings; org-wide flow budgets; org rules.
  - Repository- and Team- scoped rules (team paths/role match overrides).
  - Risk scoring and auto-approvals grounded in assessed readiness.
  - Lock repo-level ties via tool hooks for safety.
- Safe Experimentation with Verify:
  - Behavior verification executes in sandboxed environment using special “spectre” spies.
  - Only synthetic or controlled tests; no external access to prod/dev other than the repo.
  - Users approve/inspect; artifacts reviewed without LLM exposure.

### Why It's 'Perfect' & Intact

- Guardrails:
  - No LLM writes to repos via git (writes via CLI/UI are separate).
  - Tools don't trust LLM prompts blindly; tool behaviors are deterministic.
  - Multi-pronged existence: SAST scores without LLM; base flaw scores; git flattening; Knowledge Graph as safety net.
- Coupled product feedback loop:
  - 50K+ repos experience daily; design iterates fast.
  - Safety bug bounty; security teams, SOC 2 audit ensure strict compliance.
  - Unified ConOps + train-year X deepest eyes.
- Trip-wire design:
  - Analyzer seeds and Deep Scan level updates (private signal) flag movements.
  - Danger-symbols list optionally blocks code changes; compliance at code level.


## 10. What You'd Need to Build Something Like CodeRabbit

### 1. Core Infrastructure

- Git introspection layer:
  - Implement git cloning, branch fetching, diff generation.
  - Cache repo state locally for offline analysis.
  - Maintain commit history and gotchas (authorship, peaks, trunchs).
- LLM orchestration:
  - Use an appropriate LLM (e.g., GPT-4o, Claude Opus, custom built).
  - Provide chain-of-thought prompting: "reason step by step" and "ground your assessment in artifacts".
  - Keep prompts short and anchored to artifacts (diff artifacts + analyzer logs + knowledge base + custom check annotations).
- Multi-tool analyzer harness:
  - Decide between:
    - Embed via commissioning: Strict Docker/Jailkit/sandbox; each analyzer runs in its own process.
    - Embedded as "included": Riskier; assume tool trust.
  - Design strategy: Analyzers write logs to temp directories; parse core score, severity per issue; feed into LLM for contextual comment.
- Knowledge Graph:
  - Schema: repo ↔ files ↔ symbols ↔ patterns ↔ issues.
  - Nodes: commit, PR, repo, user, file, symbol.
  - Annotate with labels, index for retrieval.
  - Use as retrieval corpus for guided review; iron out unique patterns (e.g., "old API still in use").

### 2. SaaS vs Self-host’d

- SaaS:
  - Frontend Next.js-like SPA.
  - Backend with per-seat flow budgets per-org.
  - Rate-limiting to prevent abuse.
  - Metric sharding (per-org, per-repo).
- Self-hosted (Cloud Ops):
  - Docker/compose; GitHub integration (App registering).
  - OAuth setup; per-org/server config.
  - Run auth tokens; prevent forking without config.

### 3. Core Features to Implement

#### Review Pipeline
- Before LLM:
  - Run analyzer tools.
  - Compute base flaw scores.
  - Perform static analysis (SAST, security).
- LLM Query:
  - Provide data in structured format: diff, analyzer logs, rules, custom checks, knowledge base snippets, context.
  - Prompt:
    - Reason through the change.
    - Identify issues with severity.
    - Give suggestions with examples and links to guidelines.
  - If analyzer already flagged: Use as scaffolding; LLM determines final findings and context.
- Post-LLM:
  - Thread mapping (issue ↔ related files ↔ user).
  - Status review (requires approve: highest review, warning on dangerous symbols).
  - Chat guidance (Reviewer/Builder). Provide default prompts.

#### Configuration (V2-style YAML)
- JSON/YAML schema; versioning; migration path.
- Language profile (tone_instructions).
- Auto-review toggles and enforcement.
- Auto-approval toggles with risk checks + severity constraints.

#### Intellisense Guides
- Provide "unsafe symbols" list (or per-repo flags).
- Danger-symbols detection flagged by analyzer; if present, block unless overridden.

#### Deep Scan
- Seeds: pre-existing security thresholds; Deep Scan improvement triggers only if score improves.
- Run Deep Scan; compare to seeded score; compute improved scores; classify.

#### Triage
- Build a cross-repository queue; implement scoring metrics.
- Fields:
  - Severity of CodeRabbit findings.
  - Urgency from external issue (Linear/Jira).
  - Downstream blocked PRs (git graph dependency).
- Attention Score per reviewer: action ownership, time handoff.last_update, recent activity, waiting pressure.

#### Verify (Device/Sandbox)
- Device/emulator attach; instrumentation in-silica e2e; when user clicks "Verify" the sandbox is spun up.
- Don't give tests access to prod; only controlled test environment.
- Boards: Generate coverage, recordings, logs; provide them to reviewer; don't expose LLM.

#### Plan Engine (Planning)
- Parse Issue → CodeRabbit Plan:
  - Research: Use Knowledge Graph; find relevant files, patterns.
  - Design Choices: List decisions.
  - Phases and Tasks.
  - Agent Prompt: structure prompts for downstream coding agents.
- If customers want agent-safe prompts: Use separate “Plan Output” model; only generate prompts.

#### Integrations
- GitHub App:
  - Install manifest registration; repo watchers; webhooks (PR opened, pushed, labelled).
- GitHub vs GitLab vs Azure DevOps vs Bitbucket:
  - Keep provider-agnostic contract for push/post-change webhooks.
- Slack Agent:
  - Slack App; post PR context; user clicks to view.
- CLI:
  - Generate tokens via cli get-token.
  - CLI commands for pull requests: coderabbit create, coderabbit verify, coderabbit exec.
  - Cache repo per call for offline analysis; manage caches.

### 4. Safety & Security

- Repo keys vs identity: never give LLM access to repo access tokens; just log-level repository details (via git introspection).
- Flow budgeting:
  - Per-org; per-seat.
  - Reject API calls if over budget.
- Compliance:
  - SOC 2 Type II (if SaaS).
  - Data retention policy; selection of TIER policies.

### 5. Extensibility

- Templates:
  - Provide templates for custom analyzers with documentation.
  - Tool definitions (e.g., custom rulset) via templates.
- MCP & Plugins:
  - Provide MCP + web UI, but if customers want to bring their own: path permissions.
- APNs/Monitoring:
  - OpenTelemetry counters + Prometheus metrics for self-host.


## 11. Key Design Principles (How It Ends Up as a "Gem")

Grounded Reasoning:
- Multi-source: analyzer outputs + codebase knowledge + guidelines + custom checks.
- Avoid hallucinations: anchor response to specific artifacts; use KGR as constant.

Deterministic & Predictable:
- Base flaw scores from tools; non-LLM-first.
- Prioritization algorithm is deterministic scoring model.
- Admin rules override, but don't bypass base scoring.

Role-Aware UX:
- Builder mode: define guidelines; safe to experiment.
- Reviewer mode: use designed guides for deep analysis.
- Triage: per-user attention queue.

Cost-Safe Practice:
- Per-stage flow budgets; per-seat.
- Per-PR cost limits; org-level safety caps.
- Deep Scan improves safety scores only when improvement is genuine.

Privacy-First, but Reasonable:
- Transmit-only LLM; no LLM writes.
- Safe Sandbox for Verify.
- Never store training data; data deletion on request.
- Explicit alerts for unsafe symbols.

Open-Minded but Guardrails:
- Integrations easy to install; but integrations obey config.
- Template system; meta-analysis for safeness; heavy but beneficial.

Agentic Stack:
- Triage + Plan + Verify + Chat + IDE + CLI form a cohesive product stack.
- New features can natively interact across components.

### The Golden Principles

1. Inputs Only = Outputs Only: LLM only reads repo; writes only via UI/git hooks; you maintain the gate.
2. Analyzer Weights: Multi-tool analyzers are first-order gate; LLM decides final relevance/categorization.
3. Knowledge Graph = Audit Trail: Repo-level KGR captures every change; grounding is versioned.
4. Triage = Value over Urgency: Not FIFO by arrival; scored by severity, urgency, downstream.
5. Invariant of Safety: Every safety operation (Verify, DeepScan) must be user-understandable, controllable, and detection-based.
6. Easy Integration: Install GitHub app overnight; use CLI offline; use VS Code today.
7. Fail-Fast on Ban: "unsafe symbols" list blocks code changes entirely; never let a model bypass.

If you build your own implementation anchored in these principles, you too can achieve the CodeRabbit experience: a "gem" that feels like a second pair of expert eyes, always-on, grounded, reliable, and irreducibly collaborative.
