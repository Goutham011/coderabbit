"""Coderabbit CLI package — AI-powered code review for agents."""
from coderabbit.models import Finding, ReviewResult, Severity
from coderabbit.config import Config
from coderabbit.knowledge_base import KnowledgeBase
from coderabbit.planner import Planner, Plan
from coderabbit.review import ReviewEngine
from coderabbit.triage import PRItem, TriageQueue, ReviewerScore
from coderabbit.sandbox import SandboxManager, SandboxResult

__all__ = ["Finding", "ReviewResult", "Severity", "Config", "KnowledgeBase", "Planner", "Plan", "ReviewEngine", "PRItem", "TriageQueue", "ReviewerScore", "SandboxManager", "SandboxResult"]
__version__ = "0.6.0"