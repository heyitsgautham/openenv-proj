"""Shared grading helpers for deterministic task scoring."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable, List, Sequence

_NULL_TOKENS = {"n/a", "na", "null", "none", "-", "--"}
_DEFAULT_DATE_FORMATS = (
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%m/%d/%Y",
    "%B %d %Y",
    "%b %d %Y",
)
_SCORE_EPSILON = 1e-3


def clamp_score(score: float) -> float:
    """Clamp any numeric-like score into the strict-open range (0.0, 1.0)."""
    try:
        value = float(score)
    except (TypeError, ValueError):
        return _SCORE_EPSILON
    bounded = max(0.0, min(1.0, value))
    return max(_SCORE_EPSILON, min(1.0 - _SCORE_EPSILON, bounded))


def normalize_string(value: Any, null_tokens: Iterable[str] | None = None) -> str:
    """Normalize text by trimming, lowercasing, and collapsing whitespace."""
    text = " ".join(str(value or "").strip().lower().split())
    tokens = set(_NULL_TOKENS if null_tokens is None else null_tokens)
    if text in tokens:
        return ""
    return text


def normalize_phone(value: Any) -> str:
    """Normalize phone values to 10-digit XXX-XXX-XXXX when possible."""
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    if len(digits) >= 10:
        digits = digits[-10:]
        return f"{digits[0:3]}-{digits[3:6]}-{digits[6:10]}"
    return digits


def normalize_date(value: Any, date_formats: Sequence[str] | None = None) -> str:
    """Normalize date values to ISO format when parsing is possible."""
    raw = str(value or "").strip()
    if not raw:
        return ""

    formats = _DEFAULT_DATE_FORMATS if date_formats is None else tuple(date_formats)
    for fmt in formats:
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue

    return normalize_string(raw, null_tokens=())


def parse_float(value: Any) -> float | None:
    """Parse currency-like numeric values into float."""
    if value is None:
        return None

    raw = str(value).strip()
    if raw == "":
        return None

    cleaned = raw.replace("$", "").replace(",", "")
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_int(value: Any) -> int | None:
    """Parse integer-like values using deterministic conversion."""
    if value is None:
        return None

    raw = str(value).strip()
    if raw == "":
        return None

    try:
        return int(float(raw))
    except ValueError:
        return None


def normalize_tags(value: Any) -> List[str]:
    """Normalize list-like tags into a sorted unique list."""
    if isinstance(value, list):
        tags = [normalize_string(item, null_tokens=()) for item in value]
    elif value is None:
        tags = []
    else:
        tags = [normalize_string(part, null_tokens=()) for part in str(value).split(",")]

    cleaned = [tag for tag in tags if tag]
    return sorted(set(cleaned))


def numeric_match(
    expected: Any,
    actual: Any,
    *,
    abs_tol: float = 1.0,
    rel_tol: float = 0.01,
    zero_abs_tol: float = 0.01,
) -> bool:
    """Compare numerics with absolute and relative tolerance bounds."""
    expected_num = parse_float(expected)
    actual_num = parse_float(actual)
    if expected_num is None or actual_num is None:
        return False

    if expected_num == 0:
        return abs(actual_num) <= zero_abs_tol

    abs_diff = abs(expected_num - actual_num)
    rel_diff = abs_diff / abs(expected_num)
    return abs_diff <= abs_tol and rel_diff <= rel_tol


def compare_field(expected: Any, actual: Any, field_type: str = "string") -> bool:
    """Type-aware field comparison helper used by task graders."""
    if expected is None and actual is None:
        return True
    if expected is None or actual is None:
        return False

    if field_type == "numeric":
        return numeric_match(expected, actual)

    if field_type == "integer":
        return parse_int(expected) == parse_int(actual)

    if field_type == "date":
        return normalize_date(expected) == normalize_date(actual)

    if field_type == "phone":
        return normalize_phone(expected) == normalize_phone(actual)

    if field_type == "tags":
        return normalize_tags(expected) == normalize_tags(actual)

    return normalize_string(expected, null_tokens=()) == normalize_string(actual, null_tokens=())


def format_error(code: str, **fields: Any) -> str:
    """Create deterministic, code-prefixed validation error strings."""
    if not fields:
        return code

    parts = [code]
    for name in sorted(fields):
        value = fields[name]
        if isinstance(value, list):
            value_text = ",".join(str(item) for item in value)
        elif value is None:
            value_text = ""
        else:
            value_text = str(value)

        safe = value_text.replace("|", "/").replace("\n", " ").strip()
        parts.append(f"{name}={safe}")

    return "|".join(parts)


def append_error(errors: List[str], max_errors: int, code: str, **fields: Any) -> None:
    """Append a formatted error while respecting the per-grade cap."""
    if len(errors) >= max_errors:
        return
    errors.append(format_error(code, **fields))


def grade_submission(task: Any, submitted_data: List[Dict[str, Any]]) -> Any:
    """Run a task-specific grader and enforce score clamping."""
    result = task.grade(submitted_data)
    result.score = clamp_score(result.score)
    return result


__all__ = [
    "append_error",
    "clamp_score",
    "compare_field",
    "format_error",
    "grade_submission",
    "normalize_date",
    "normalize_phone",
    "normalize_string",
    "normalize_tags",
    "numeric_match",
    "parse_float",
    "parse_int",
]
