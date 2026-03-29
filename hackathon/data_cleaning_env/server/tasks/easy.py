"""Easy task definition for deterministic basic data cleaning."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

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
    text = str(value or "").strip().lower()
    if text in {"n/a", "na", "null", "none", "-", "--"}:
        return ""
    return text


def _norm_phone(value: Any) -> str:
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    if len(digits) >= 10:
        digits = digits[-10:]
        return f"{digits[0:3]}-{digits[3:6]}-{digits[6:10]}"
    return digits


def _norm_date(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%B %d %Y", "%b %d %Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue
    return raw.lower()


def _norm_amount(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return "0.00"
    cleaned = raw.replace("$", "").replace(",", "")
    try:
        return f"{float(cleaned):.2f}"
    except ValueError:
        return cleaned.lower()


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
        errors: List[str] = []
        if not isinstance(submitted, list):
            return GradeResult(
                score=0.0,
                correct_fields=0,
                total_fields=self.total_gradable_fields,
                errors=["Submission must be a list of records."],
            )

        submitted_records = [_normalize_record(row) for row in submitted if isinstance(row, dict)]

        expected_map: Dict[str, Dict[str, str]] = {}
        for row in self._expected_data:
            expected_map[_record_key(row)] = row

        submitted_map: Dict[str, Dict[str, str]] = {}
        duplicate_keys = set()
        for row in submitted_records:
            key = _record_key(row)
            if key in submitted_map:
                duplicate_keys.add(key)
            submitted_map[key] = row

        correct_fields = 0
        for key, expected in expected_map.items():
            actual = submitted_map.get(key)
            if actual is None:
                if len(errors) < 25:
                    errors.append(f"Missing expected record: {key}")
                continue

            for field in _FIELDS:
                if actual.get(field) == expected.get(field):
                    correct_fields += 1
                elif len(errors) < 25:
                    errors.append(f"Mismatch for {key} field '{field}'.")

        if duplicate_keys and len(errors) < 25:
            errors.append(f"Duplicate records found for keys: {sorted(duplicate_keys)[:3]}")

        extra_keys = sorted(set(submitted_map.keys()) - set(expected_map.keys()))
        if extra_keys and len(errors) < 25:
            errors.append(f"Unexpected extra records: {extra_keys[:3]}")

        total_fields = self.total_gradable_fields
        score = (correct_fields / total_fields) if total_fields else 0.0
        score = max(0.0, min(1.0, score))

        return GradeResult(
            score=score,
            correct_fields=correct_fields,
            total_fields=total_fields,
            errors=errors,
        )
