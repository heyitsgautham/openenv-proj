"""Easy task definition for deterministic basic data cleaning."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from ..graders import (
    append_error,
    clamp_score,
    normalize_date,
    normalize_phone,
    normalize_string,
    parse_float,
)
from .base import BaseTask, GradeResult

_DATA_DIR = Path(__file__).resolve().parent / "data"
_FIELDS = [
    "name",
    "email",
    "phone",
    "date_of_birth",
    "status",
    "amount",
    "category",
    "notes",
]


def _load_json_list(filename: str) -> List[Dict[str, Any]]:
    path = _DATA_DIR / filename
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Missing task data file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in task data file: {path}") from exc

    if not isinstance(payload, list):
        raise ValueError(f"Expected list payload in task data file: {path}")
    return payload


def _norm_text(value: Any) -> str:
    return normalize_string(value)


def _norm_phone(value: Any) -> str:
    return normalize_phone(value)


def _norm_date(value: Any) -> str:
    return normalize_date(value)


def _norm_amount(value: Any) -> str:
    parsed = parse_float(value)
    if parsed is None:
        raw = str(value or "").strip()
        if not raw:
            return "0.00"
        return normalize_string(raw, null_tokens=())

    return f"{parsed:.2f}"


def _submission_records(submitted: List[Any], errors: List[str], max_errors: int) -> List[Dict[str, str]]:
    records: List[Dict[str, str]] = []
    for index, row in enumerate(submitted):
        if not isinstance(row, dict):
            append_error(
                errors,
                max_errors,
                "SCHEMA_ERROR",
                detail="item_not_object",
                record=index,
            )
            continue
        records.append(_normalize_record(row))
    return records


def _as_ordered_map(rows: List[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    mapped: Dict[str, Dict[str, str]] = {}
    for row in rows:
        mapped[_record_key(row)] = row
    return mapped


class EasyTask(BaseTask):
    """Basic cleaning task with deterministic field-level grading."""

    def __init__(self) -> None:
        self.task_id = "easy"
        self.description = (
            "Clean messy customer records by normalizing values and removing exact duplicates."
        )
        self.max_steps = 10
        self.input_data = _load_json_list("easy_input.json")
        self._expected_data = [_normalize_record(row) for row in _load_json_list("easy_expected.json")]
        self.expected_data = self._expected_data
        self.gold_data = self._expected_data
        self.target_schema = {
            "name": "string",
            "email": "string",
            "phone": "string",
            "date_of_birth": "date",
            "status": "string",
            "amount": "number",
            "category": "string",
            "notes": "string",
        }
        self.total_gradable_fields = len(self._expected_data) * len(_FIELDS)

    def grade(self, submitted: List[Dict[str, Any]]) -> GradeResult:
        max_errors = 25
        if not isinstance(submitted, list):
            return GradeResult(
                score=0.0,
                correct_fields=0,
                total_fields=self.total_gradable_fields,
                errors=["SCHEMA_ERROR|detail=submission_must_be_list|record=root"],
            )

        errors: List[str] = []
        submitted_records = _submission_records(submitted, errors, max_errors)

        expected_map = _as_ordered_map(self._expected_data)

        submitted_map: Dict[str, Dict[str, str]] = {}
        duplicate_keys = set()
        for row in submitted_records:
            key = _record_key(row)
            if key in submitted_map:
                duplicate_keys.add(key)
            submitted_map[key] = row

        correct_fields = 0
        for key in sorted(expected_map):
            expected = expected_map[key]
            actual = submitted_map.get(key)
            if actual is None:
                append_error(errors, max_errors, "MISSING_RECORD", key=key)
                continue

            for field in _FIELDS:
                expected_value = expected.get(field, "")
                actual_value = actual.get(field, "")
                if actual_value == expected_value:
                    correct_fields += 1
                else:
                    append_error(
                        errors,
                        max_errors,
                        "MISMATCH",
                        actual=actual_value,
                        expected=expected_value,
                        field=field,
                        key=key,
                    )

        for key in sorted(duplicate_keys):
            append_error(errors, max_errors, "DUPLICATE_RECORD", key=key)

        for key in sorted(set(submitted_map.keys()) - set(expected_map.keys())):
            append_error(errors, max_errors, "EXTRA_RECORD", key=key)

        total_fields = self.total_gradable_fields
        score = clamp_score((correct_fields / total_fields) if total_fields else 0.0)

        return GradeResult(
            score=score,
            correct_fields=correct_fields,
            total_fields=total_fields,
            errors=errors,
        )


def _normalize_record(record: Dict[str, Any]) -> Dict[str, str]:
    return {
        "name": _norm_text(record.get("name")),
        "email": _norm_text(record.get("email")),
        "phone": _norm_phone(record.get("phone")),
        "date_of_birth": _norm_date(record.get("date_of_birth")),
        "status": _norm_text(record.get("status")),
        "amount": _norm_amount(record.get("amount")),
        "category": _norm_text(record.get("category")),
        "notes": _norm_text(record.get("notes")),
    }


def _record_key(record: Dict[str, str]) -> str:
    if record.get("email"):
        return f"email:{record['email']}"
    if record.get("phone"):
        return f"phone:{record['phone']}"
    return f"name:{record.get('name', '')}|dob:{record.get('date_of_birth', '')}"
