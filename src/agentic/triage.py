"""Triage queue — cross-repo PR prioritization."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Optional


# Scoring weights from pipeline specification
SEVERITY_WEIGHT = 10
URGENCY_WEIGHT = 5
BLOCKED_WEIGHT = 3
VALUE_WEIGHT = 2
EFFORT_WEIGHT = 1


@dataclass
class PRItem:
    """Pull request entry in the triage queue."""

    repo: str
    pr_number: int
    title: str
    author: str = ""
    severity: float = 0.0
    external_urgency: int = 0
    downstream_blocked: int = 0
    change_value: int = 1
    review_effort: int = 0
    labels: list[str] = field(default_factory=list)

    @property
    def priority_score(self) -> float:
        """Calculate priority using weighted scoring formula."""
        return (
            self.severity * SEVERITY_WEIGHT
            + self.external_urgency * URGENCY_WEIGHT
            + self.downstream_blocked * BLOCKED_WEIGHT
            + self.change_value * VALUE_WEIGHT
            - self.review_effort * EFFORT_WEIGHT
        )

    @classmethod
    def from_dict(cls, data: dict) -> "PRItem":
        """Create PRItem from dictionary payload."""
        return cls(
            repo=data.get("repo", ""),
            pr_number=data.get("pr_number", 0),
            title=data.get("title", ""),
            author=data.get("author", ""),
            severity=float(data.get("severity", 0)),
            external_urgency=int(data.get("external_urgency", 0)),
            downstream_blocked=int(data.get("downstream_blocked", 0)),
            change_value=int(data.get("change_value", 1)),
            review_effort=int(data.get("review_effort", 0)),
            labels=data.get("labels", []),
        )

    def to_dict(self) -> dict:
        """Serialize to dictionary for JSON output."""
        return {
            "repo": self.repo,
            "pr_number": self.pr_number,
            "title": self.title,
            "author": self.author,
            "severity": self.severity,
            "external_urgency": self.external_urgency,
            "downstream_blocked": self.downstream_blocked,
            "change_value": self.change_value,
            "review_effort": self.review_effort,
            "priority_score": round(self.priority_score, 2),
            "queue": self.queue_position,
            "labels": self.labels,
        }

    @property
    def queue_position(self) -> str:
        """Return Now or Next based on score threshold."""
        if self.priority_score >= 15:
            return "now"
        if self.priority_score >= 8:
            return "next"
        return "later"


@dataclass
class ReviewerScore:
    """Attention metric per reviewer."""

    name: str
    pending_count: int = 0
    avg_wait_days: float = 0.0

    @property
    def attention_score(self) -> float:
        """Calculate attention score from workload metrics."""
        return self.pending_count * 5 + self.avg_wait_days * 10


class TriageQueue:
    """Cross-repo PR priority queue."""

    def __init__(self, items: list[PRItem] | None = None):
        self._items: list[PRItem] = sorted(items or [], key=lambda x: x.priority_score, reverse=True)

    def add(self, item: PRItem) -> None:
        """Insert single PR and re-sort queue."""
        self._items.append(item)
        self._items.sort(key=lambda x: x.priority_score, reverse=True)

    def batch_add(self, items: list[PRItem]) -> None:
        """Insert multiple PRs and re-sort once."""
        self._items.extend(items)
        self._items.sort(key=lambda x: x.priority_score, reverse=True)

    def filter_by_org(self, org: str) -> "TriageQueue":
        """Return subset filtered to one organization."""
        return TriageQueue([item for item in self._items if item.repo.startswith(org)])

    def split_queues(self) -> tuple[list[PRItem], list[PRItem], list[PRItem]]:
        """Split into now/next/later queues."""
        now: list[PRItem] = []
        next_queue: list[PRItem] = []
        later: list[PRItem] = []
        for item in self._items:
            if item.queue_position == "now":
                now.append(item)
            elif item.queue_position == "next":
                next_queue.append(item)
            else:
                later.append(item)
        return now, next_queue, later

    def to_json(self) -> str:
        """Serialize entire queue to JSON string."""
        data = {
            "total_prs": len(self._items),
            "now_count": sum(1 for i in self._items if i.queue_position == "now"),
            "next_count": sum(1 for i in self._items if i.queue_position == "next"),
            "later_count": sum(1 for i in self._items if i.queue_position == "later"),
            "prs": [item.to_dict() for item in self._items],
        }
        return json.dumps(data, indent=2)

    def to_markdown(self) -> str:
        """Render queue as Markdown table."""
        lines = ["# Triage Queue", ""]
        now, next_queue, later = self.split_queues()
        lines.extend(["## Now", "", "| Priority | Repo | PR | Title | Score |"])
        lines.append("|----------|------|----|-------|-------|")
        for item in now:
            lines.append(f"| {item.queue_position} | {item.repo} | #{item.pr_number} | {item.title} | {item.priority_score:.1f} |")
        lines.extend(["", "## Next", "", "| Priority | Repo | PR | Title | Score |"])
        lines.append("|----------|------|----|-------|-------|")
        for item in next_queue:
            lines.append(f"| {item.queue_position} | {item.repo} | #{item.pr_number} | {item.title} | {item.priority_score:.1f} |")
        return "\n".join(lines)

    def __len__(self) -> int:
        return len(self._items)

    def __getitem__(self, index: int) -> PRItem:
        return self._items[index]
