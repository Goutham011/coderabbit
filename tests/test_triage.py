"""Tests for the triage engine."""
import pytest
import json
from coderabbit.triage import PRItem, TriageQueue, ReviewerScore


class TestPRItem:
    def test_priority_score_formula(self):
        item = PRItem(
            repo="test/repo",
            pr_number=1,
            title="Fix bug",
            severity=0.8,
            external_urgency=2,
            downstream_blocked=1,
            change_value=3,
            review_effort=1,
        )
        expected = (0.8 * 10) + (2 * 5) + (1 * 3) + (3 * 2) - (1 * 1)
        assert item.priority_score == expected

    def test_queue_position_now(self):
        item = PRItem(repo="r", pr_number=1, title="t", severity=1.0, external_urgency=5, downstream_blocked=5)
        assert item.queue_position == "now"

    def test_queue_position_next(self):
        item = PRItem(repo="r", pr_number=1, title="t", severity=0.8, external_urgency=1, downstream_blocked=0, change_value=0)
        assert item.queue_position == "next"

    def test_queue_position_later(self):
        item = PRItem(repo="r", pr_number=1, title="t", severity=0.1, external_urgency=0, downstream_blocked=0, change_value=0)
        assert item.queue_position == "later"

    def test_from_dict(self):
        data = {"repo": "a/b", "pr_number": 5, "title": "Test", "severity": 0.7, "external_urgency": 2}
        item = PRItem.from_dict(data)
        assert item.repo == "a/b"
        assert item.pr_number == 5
        assert item.severity == 0.7

    def test_to_dict_contains_score(self):
        item = PRItem(repo="x/y", pr_number=10, title="Fix X")
        d = item.to_dict()
        assert d["repo"] == "x/y"
        assert "priority_score" in d
        assert "queue" in d

    def test_empty_pr_scores_two(self):
        item = PRItem(repo="", pr_number=0, title="")
        assert item.priority_score == 2.0


class TestTriageQueue:
    def test_sorts_by_priority_descending(self):
        low = PRItem(repo="a", pr_number=1, title="low", severity=0.1)
        high = PRItem(repo="b", pr_number=2, title="high", severity=0.9)
        queue = TriageQueue([low, high])
        assert queue[0] is high
        assert queue[1] is low

    def test_add_inserts_in_order(self):
        queue = TriageQueue()
        queue.add(PRItem(repo="a", pr_number=1, title="t", severity=0.3))
        queue.add(PRItem(repo="b", pr_number=2, title="t", severity=0.8))
        assert queue[0].severity == 0.8

    def test_batch_add_sorted(self):
        items = [
            PRItem(repo="a", pr_number=i, title="t", severity=float(i) * 0.1)
            for i in range(5)
        ]
        queue = TriageQueue()
        queue.batch_add(items)
        assert queue[0].severity >= queue[-1].severity

    def test_filter_by_org(self):
        queue = TriageQueue([
            PRItem(repo="acme/core", pr_number=1, title="t"),
            PRItem(repo="other/lib", pr_number=2, title="t"),
            PRItem(repo="acme/api", pr_number=3, title="t"),
        ])
        filtered = queue.filter_by_org("acme")
        assert len(filtered) == 2
        assert all(p.repo.startswith("acme") for p in filtered)

    def test_split_queues_into_three(self):
        items = [
            PRItem(repo="a", pr_number=1, title="t", severity=1.0, external_urgency=1, change_value=0),
            PRItem(repo="b", pr_number=2, title="t", severity=0.5, external_urgency=1, change_value=0),
            PRItem(repo="c", pr_number=3, title="t", severity=0.1, change_value=0),
        ]
        queue = TriageQueue(items)
        now, next_q, later = queue.split_queues()
        assert len(now) == 1
        assert len(next_q) == 1
        assert len(later) == 1

    def test_to_json_serializes_correctly(self):
        queue = TriageQueue([
            PRItem(repo="x/y", pr_number=1, title="Fix auth", severity=0.8),
        ])
        data = json.loads(queue.to_json())
        assert data["total_prs"] == 1
        assert len(data["prs"]) == 1

    def test_to_markdown_has_sections(self):
        queue = TriageQueue([
            PRItem(repo="a/b", pr_number=1, title="High prio", severity=0.9),
            PRItem(repo="c/d", pr_number=2, title="Low prio", severity=0.1),
        ])
        md = queue.to_markdown()
        assert "Now" in md
        assert "Next" in md
        assert "a/b" in md

    def test_len_returns_count(self):
        queue = TriageQueue([
            PRItem(repo="a", pr_number=1, title="t"),
            PRItem(repo="b", pr_number=2, title="t"),
        ])
        assert len(queue) == 2

    def test_getitem_accesses_by_index(self):
        queue = TriageQueue([
            PRItem(repo="a", pr_number=1, title="first"),
            PRItem(repo="b", pr_number=2, title="second"),
        ])
        assert queue[0].title == "first"
        assert queue[1].title == "second"


class TestReviewerScore:
    def test_attention_score_calculation(self):
        r = ReviewerScore(name="alice", pending_count=5, avg_wait_days=2.0)
        assert r.attention_score == 5 * 5 + 2.0 * 10

    def test_default_values(self):
        r = ReviewerScore(name="bob")
        assert r.pending_count == 0
        assert r.avg_wait_days == 0.0
        assert r.attention_score == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
