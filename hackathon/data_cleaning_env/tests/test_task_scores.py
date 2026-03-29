"""Task-level score spread and determinism tests for Session 3."""

from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.tasks import TASK_REGISTRY

_ALLOWED_ERROR_PREFIXES = {
    "SCHEMA_ERROR",
    "MISSING_RECORD",
    "MISMATCH",
    "DUPLICATE_RECORD",
    "EXTRA_RECORD",
}


def _gold_payload(task):
    for attr in ("expected_data", "gold_data", "_expected_data"):
        value = getattr(task, attr, None)
        if isinstance(value, list):
            return value
    return []


def _partial_payload(gold):
    if not isinstance(gold, list) or not gold:
        return []
    return gold[: max(1, len(gold) // 2)]


@pytest.mark.parametrize("task_id", sorted(TASK_REGISTRY.keys()))
def test_expected_payload_alias_available(task_id: str) -> None:
    task = TASK_REGISTRY[task_id]
    expected_data = getattr(task, "expected_data", None)
    assert isinstance(expected_data, list)


@pytest.mark.parametrize("task_id", sorted(TASK_REGISTRY.keys()))
def test_score_bounds_and_spread(task_id: str) -> None:
    task = TASK_REGISTRY[task_id]
    gold = _gold_payload(task)
    partial = _partial_payload(gold)

    empty_result = task.grade([])
    partial_result = task.grade(partial)
    perfect_result = task.grade(gold)

    assert 0.0 <= empty_result.score <= 1.0
    assert 0.0 <= partial_result.score <= 1.0
    assert 0.0 <= perfect_result.score <= 1.0

    assert empty_result.score <= 0.05
    assert perfect_result.score >= 0.95
    assert empty_result.score < partial_result.score < perfect_result.score


@pytest.mark.parametrize("task_id", sorted(TASK_REGISTRY.keys()))
def test_deterministic_replay_same_input_same_output(task_id: str) -> None:
    task = TASK_REGISTRY[task_id]
    gold = _gold_payload(task)
    payload = _partial_payload(gold)

    first = task.grade(payload)
    second = task.grade(payload)

    assert first.score == second.score
    assert first.correct_fields == second.correct_fields
    assert first.total_fields == second.total_fields
    assert first.errors == second.errors


@pytest.mark.parametrize("task_id", sorted(TASK_REGISTRY.keys()))
def test_malformed_submission_reports_structured_errors(task_id: str) -> None:
    task = TASK_REGISTRY[task_id]
    malformed = task.grade([{"bad": "shape"}, None, 42])

    assert 0.0 <= malformed.score <= 1.0
    assert malformed.errors
    assert any(error.startswith("SCHEMA_ERROR|") for error in malformed.errors)

    for error in malformed.errors:
        prefix = error.split("|", 1)[0]
        assert prefix in _ALLOWED_ERROR_PREFIXES
