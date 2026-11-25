"""CLI entry point using Click for agent integration."""
import os
import sys
from pathlib import Path
from typing import Optional
import click
import json

from coderabbit.triage import TriageQueue
from coderabbit.sandbox import SandboxResult


@click.group()
@click.version_option(version="0.6.0", prog_name="coderabbit")
@click.option("--verbose", "-v", is_flag=True)
@click.option("--config", "-c", type=Path, default=None)
@click.option("--llm-provider", type=click.Choice(["ollama", "claude", "codex", "openai", "llama.cpp", "auto"]), default="auto", help="LLM provider for fix generation")
@click.pass_context
def cli(ctx, verbose, config, llm_provider):
    """Coderabbit — AI-powered code review CLI for agents."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["config_path"] = config
    ctx.obj["llm_provider"] = llm_provider


@cli.command()
@click.argument("repo")
@click.argument("branch", required=False, default="HEAD")
@click.option("--output", "-o", type=click.Choice(["json", "human"]), default="json")
@click.option("--profile", type=click.Choice(["chill", "assertive", "quiet"]), default="assertive")
@click.option("--baseline", type=int, default=0)
@click.option("--full-scan", is_flag=True, default=False, help="Scan entire repository instead of just changed files")
@click.option("--apply-fixes", is_flag=True, default=False, help="Apply LLM-generated fixes automatically")
@click.pass_context
def review(ctx, repo, branch, output, profile, baseline, full_scan, apply_fixes):
    """Analyze code changes and return structured findings."""
    if ctx.obj["verbose"]:
        click.echo(f"Reviewing {repo}@{branch}... ", err=True, nl=False)
    from coderabbit.review import ReviewEngine

    # Determine LLM provider
    provider = ctx.obj.get("llm_provider")
    if provider == "auto":
        provider = None  # Auto-detect in ReviewEngine

    engine = ReviewEngine(config_path=ctx.obj.get("config_path"), llm_provider=provider)
    result = engine.review(
        repo,
        branch,
        profile=profile,
        baseline=baseline,
        full_scan=full_scan,
        apply_fixes=apply_fixes,
    )
    if output == "json":
        click.echo(json.dumps(result.to_dict(), indent=2))
    else:
        _print_human_review(result)

    has_critical = any(f.severity == "critical" for f in result.findings)
    sys.exit(2 if has_critical else 0)


@cli.command()
@click.argument("source")
@click.option("--output", "-o", type=click.Choice(["json", "md", "agent-prompt"]), default="json")
@click.option("--repo-path", "-r", type=Path, default=None, help="Path to index for research")
@click.option("--llm-provider", type=click.Choice(["ollama", "claude", "codex", "openai", "auto"]), default=None)
def plan(source, output, repo_path, llm_provider):
    """Generate implementation plan from issue or spec."""
    from coderabbit.planner import Planner
    from coderabbit.knowledge_base import KnowledgeBase

    kb = KnowledgeBase() if repo_path else None
    if kb and repo_path and repo_path.exists():
        kb.index_repo(repo_path, "python")
    planner = Planner(kb=kb)
    result = planner.plan(source, output)
    if kb:
        kb.close()
    if output == "json":
        click.echo(json.dumps(result.to_dict(), indent=2))
    elif output == "md":
        click.echo(result.to_markdown())
    else:
        click.echo(result.prompt)


@cli.command()
@click.argument("repo")
@click.argument("branch", required=False, default="HEAD")
@click.option("--test-type", type=click.Choice(["unit", "e2e", "integration"]), default="unit")
@click.option("--output", "-o", type=click.Choice(["json", "human"]), default="json")
@click.option("--timeout", type=int, default=None, help="Test timeout in seconds (default: 180)")
def verify(repo, branch, test_type, output, timeout):
    """Run sandboxed tests for PR behavior validation."""
    from coderabbit.sandbox import SandboxManager
    mgr = SandboxManager()
    try:
        result = mgr.run_tests(repo, branch, test_type, timeout=timeout)
        if output == "json":
            click.echo(json.dumps(result.to_dict(), indent=2))
        else:
            _print_verify_result(result)
        sys.exit(0 if result.success else 1)
    finally:
        mgr.close()


def _print_verify_result(result: SandboxResult) -> None:
    from rich.console import Console
    console = Console()
    console.print(f"\n[dim]Command:[/dim] {result.command}")
    status = "PASS" if result.success else "FAIL"
    color = "green" if result.success else "red"
    console.print(f"[bold {color}]Status: {status}[/bold {color}]  Return code: {result.returncode}")
    console.print(f"[dim]Duration:[/dim] {result.duration_seconds:.1f}s  [dim]Sandbox:[/dim] {result.sandbox_mode}")
    if result.stdout:
        console.print(f"\n[dim]stdout (first 4 KB):[/dim]\n{result.stdout[:4096]}")
    if result.stderr:
        console.print(f"\n[dim]stderr (first 4 KB):[/dim]\n{result.stderr[:4096]}")
    artifacts = result.artifacts
    if artifacts:
        console.print("\n[dim]Artifacts:[/dim]")
        for key, val in artifacts.items():
            console.print(f"  {key}: {val}")


@cli.command()
@click.option("--org", "-g", default=None, help="Filter by organization")
@click.option("--format", "-f", type=click.Choice(["table", "json", "md"]), default="table")
def triage(org, format):
    """Show prioritized PR queue."""
    from coderabbit.triage import TriageQueue, PRItem
    sample_prs = [
        PRItem(repo="acme/core", pr_number=42, title="Fix auth bypass vulnerability", author="alice", severity=0.9, external_urgency=3, downstream_blocked=2, change_value=5, review_effort=2, labels=["security", "urgent"]),
        PRItem(repo="acme/api", pr_number=87, title="Add rate limiting to endpoints", author="bob", severity=0.4, external_urgency=1, downstream_blocked=0, change_value=3, review_effort=3, labels=["feature"]),
        PRItem(repo="acme/web", pr_number=15, title="Update dependencies", author="carol", severity=0.2, external_urgency=0, downstream_blocked=1, change_value=1, review_effort=1, labels=["chore"]),
        PRItem(repo="acme/data", pr_number=203, title="Fix data migration race condition", author="dave", severity=0.7, external_urgency=2, downstream_blocked=3, change_value=4, review_effort=4, labels=["bug", "critical"]),
        PRItem(repo="acme/auth", pr_number=11, title="Refactor token validation", author="eve", severity=0.5, external_urgency=0, downstream_blocked=0, change_value=2, review_effort=5, labels=["refactor"]),
    ]
    if org:
        queue = TriageQueue(sample_prs).filter_by_org(org)
    else:
        queue = TriageQueue(sample_prs)
    if format == "json":
        click.echo(queue.to_json())
    elif format == "md":
        click.echo(queue.to_markdown())
    else:
        _print_triage_table(queue)


def _print_triage_table(queue: TriageQueue) -> None:
    """Print triage queue as aligned table."""
    now, next_queue, later = queue.split_queues()
    lines = ["# Triage Queue", "", f"Total PRs: {len(queue)}", ""]
    lines.extend(["## Now (urgent)", "", "| # | Repo | PR | Title | Author | Score |"])
    lines.append("|---|------|----|-------|--------|-------|")
    for item in now:
        lines.append(f"| {len(now) - now.index(item)} | {item.repo} | #{item.pr_number} | {item.title[:30]} | {item.author} | {item.priority_score:.1f} |")
    lines.extend(["", "## Next (standard)", "", "| # | Repo | PR | Title | Author | Score |"])
    lines.append("|---|------|----|-------|--------|-------|")
    for item in next_queue:
        lines.append(f"| {len(next_queue) - next_queue.index(item)} | {item.repo} | #{item.pr_number} | {item.title[:30]} | {item.author} | {item.priority_score:.1f} |")
    if later:
        lines.extend(["", "## Later (routine)", "", "| # | Repo | PR | Title | Score |"])
        lines.append("|---|------|----|-------|-------|")
        for item in later:
            lines.append(f"| {len(later) - later.index(item)} | {item.repo} | #{item.pr_number} | {item.title[:30]} | {item.priority_score:.1f} |")
    click.echo("\n".join(lines))


@cli.group()
def kb():
    """Knowledge base operations."""


@kb.command("index")
@click.argument("repo_path", type=Path)
@click.option("--language", "-l", default="python", help="Primary language")
def kb_index(repo_path: Path, language: str):
    """Index repository into knowledge graph."""
    from coderabbit.knowledge_base import KnowledgeBase
    if not repo_path.exists():
        click.echo(json.dumps({"error": f"Path not found: {repo_path}"}), err=True)
        sys.exit(1)
    kb = KnowledgeBase()
    result = kb.index_repo(repo_path, language)
    kb.close()
    click.echo(json.dumps({"status": "indexed", **result}, indent=2))


@kb.command("query")
@click.argument("type")
@click.argument("value")
@click.option("--language", "-l", default=None, help="Filter by language (python, javascript, etc.)")
def kb_query(type: str, value: str, language: Optional[str]):
    """Search knowledge graph."""
    from coderabbit.knowledge_base import KnowledgeBase
    kb = KnowledgeBase()
    if language:
        results = kb.query_by_language(language, type, value)
    else:
        results = kb.query(type, value)
    kb.close()
    click.echo(json.dumps({"count": len(results), "results": results}, indent=2))


@cli.group()
def token():
    """Manage authentication tokens."""


@token.command()
@click.option("--scope", type=click.Choice(["read", "read-write", "admin"]), default="read")
def generate(scope):
    """Generate new auth token."""
    import secrets
    click.echo(json.dumps({"status": "generated", "token": f"agr_{secrets.token_hex(24)}", "scope": scope, "warning": "Store securely. Not displayed again."}, indent=2))


def _print_human_review(result):
    from rich.console import Console
    console = Console()
    console.print(f"[bold]Review Results for {result.repo}@{result.branch}[/bold]")
    console.print(f"Severity: {result.overall_severity}")
    console.print(f"Findings: {len(result.findings)}")
    for finding in result.findings[:5]:
        emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵"}.get(finding.severity, "⚪")
        console.print(f"{emoji} [{finding.severity.upper()}] {finding.message}")


if __name__ == "__main__":
    cli()