"""Unit tests for shared grading helpers."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.graders import (
    append_error,
    clamp_score,
    compare_field,
    format_error,
    grade_submission,
    normalize_date,
    normalize_phone,
    normalize_string,
    normalize_tags,
)
from server.tasks.base import GradeResult


class _DummyTask:
    def grade(self, submitted):
        del submitted
        return GradeResult(score=1.5, correct_fields=0, total_fields=0, errors=[])


def test_clamp_score_bounds() -> None:
    assert 0.0 < clamp_score(-0.5) < 0.01
    assert clamp_score(0.25) == 0.25
    assert 0.99 < clamp_score(2.0) < 1.0
    assert 0.0 < clamp_score("bad") < 0.01


def test_compare_numeric_with_tolerance() -> None:
    assert compare_field("100", "100.5", field_type="numeric")
    assert not compare_field("100", "103", field_type="numeric")
    assert compare_field(0, 0.005, field_type="numeric")
    assert not compare_field(0, 0.02, field_type="numeric")


def test_normalization_helpers() -> None:
    assert normalize_string("  Alice   Smith ") == "alice smith"
    assert normalize_date("March 5 2024") == "2024-03-05"
    assert normalize_phone("(415) 555-1212") == "415-555-1212"
    assert normalize_tags([" VIP ", "vip", "Prospect"]) == ["prospect", "vip"]


def test_error_format_is_deterministic() -> None:
    first = format_error("MISMATCH", key="row-1", field="email", expected="a", actual="b")
    second = format_error("MISMATCH", actual="b", expected="a", field="email", key="row-1")
    assert first == second
    assert first.startswith("MISMATCH|")


def test_append_error_respects_cap() -> None:
    errors = []
    append_error(errors, 2, "ERR_A", key="1")
    append_error(errors, 2, "ERR_B", key="2")
    append_error(errors, 2, "ERR_C", key="3")
    assert len(errors) == 2


def test_grade_submission_clamps_score() -> None:
    result = grade_submission(_DummyTask(), submitted_data=[])
    assert 0.99 < result.score < 1.0
