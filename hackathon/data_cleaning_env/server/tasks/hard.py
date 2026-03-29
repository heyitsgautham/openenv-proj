"""Hard task definition for deterministic multi-source data reconciliation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import BaseTask, GradeResult

_DATA_DIR = Path(__file__).resolve().parent / "data"
_OUTPUT_FIELDS = [
    "entity_name",
    "email",
    "phone",
    "address",
    "city",
    "state",
    "postal_code",
    "lifetime_value",
    "contact_status",
    "metadata_tags",
]
_CONFLICT_FIELDS = ["lifetime_value", "contact_status", "metadata_tags"]


def _load_json(filename: str) -> Any:
    path = _DATA_DIR / filename
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Missing task data file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in task data file: {path}") from exc


def _norm_text(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _norm_phone(value: Any) -> str:
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    if len(digits) >= 10:
        digits = digits[-10:]
        return f"{digits[0:3]}-{digits[3:6]}-{digits[6:10]}"
    return digits


def _to_float(value: Any) -> Optional[float]:
    raw = str(value or "").strip()
    if not raw:
        return None
    cleaned = raw.replace("$", "").replace(",", "")
    try:
        return float(cleaned)
    except ValueError:
        return None


def _norm_tags(value: Any) -> List[str]:
    if isinstance(value, list):
        tags = [_norm_text(item) for item in value if str(item or "").strip()]
    elif value is None:
        tags = []
    else:
        tags = [_norm_text(part) for part in str(value).split(",") if part.strip()]
    return sorted(set(tags))


def _normalize_record(row: Dict[str, Any]) -> Dict[str, Any]:
    lifetime_value = _to_float(row.get("lifetime_value"))
    return {
        "entity_name": _norm_text(row.get("entity_name") or row.get("name")),
        "email": _norm_text(row.get("email")),
        "phone": _norm_phone(row.get("phone")),
        "address": _norm_text(row.get("address")),
        "city": _norm_text(row.get("city")),
        "state": _norm_text(row.get("state")),
        "postal_code": _norm_text(row.get("postal_code")),
        "lifetime_value": round(lifetime_value, 2) if lifetime_value is not None else None,
        "contact_status": _norm_text(row.get("contact_status")),
        "metadata_tags": _norm_tags(row.get("metadata_tags") or row.get("tags")),
    }


def _record_key(row: Dict[str, Any]) -> str:
    email = row.get("email", "")
    if email:
        return f"email:{email}"

    phone = row.get("phone", "")
    if phone:
        return f"phone:{phone}"

    return f"name:{row.get('entity_name', '')}|postal:{row.get('postal_code', '')}"


def _field_match(field: str, expected: Any, actual: Any) -> bool:
    if field == "lifetime_value":
        expected_num = _to_float(expected)
        actual_num = _to_float(actual)
        if expected_num is None or actual_num is None:
            return False
        return abs(expected_num - actual_num) <= 1.0

    if field == "metadata_tags":
        return _norm_tags(expected) == _norm_tags(actual)

    if field == "phone":
        return _norm_phone(expected) == _norm_phone(actual)

    return _norm_text(expected) == _norm_text(actual)


class HardTask(BaseTask):
    """Multi-source reconciliation task with weighted grading components."""

    def __init__(self) -> None:
        self.task_id = "hard"
        self.description = (
            "Reconcile records from three source systems using source-priority conflict rules."
        )
        self.max_steps = 20

        source_a = _load_json("hard_source_a.json")
        source_b = _load_json("hard_source_b.json")
        source_c = _load_json("hard_source_c.json")
        spec = _load_json("hard_spec.json")
        expected = _load_json("hard_expected.json")

        if not isinstance(source_a, list):
            raise ValueError("hard_source_a.json must contain a list of records")
        if not isinstance(source_b, list):
            raise ValueError("hard_source_b.json must contain a list of records")
        if not isinstance(source_c, list):
            raise ValueError("hard_source_c.json must contain a list of records")
        if not isinstance(spec, dict):
            raise ValueError("hard_spec.json must contain an object")
        if not isinstance(expected, list):
            raise ValueError("hard_expected.json must contain a list of records")

        self.source_a = source_a
        self.source_b = source_b
        self.source_c = source_c
        self.spec = spec

        self.input_data = [
            {"source": "A", **row} for row in self.source_a
        ] + [
            {"source": "B", **row} for row in self.source_b
        ] + [
            {"source": "C", **row} for row in self.source_c
        ]

        self._expected_data = [_normalize_record(row) for row in expected]
        self.target_schema = {
            "entity_name": "string",
            "email": "string",
            "phone": "string",
            "address": "string",
            "city": "string",
            "state": "string",
            "postal_code": "string",
            "lifetime_value": "number",
            "contact_status": "string",
            "metadata_tags": "array[string]",
        }
        self.total_gradable_fields = len(self._expected_data) * len(_OUTPUT_FIELDS)

    def grade(self, submitted: List[Dict[str, Any]]) -> GradeResult:
        if not isinstance(submitted, list):
            return GradeResult(
                score=0.0,
                correct_fields=0,
                total_fields=self.total_gradable_fields,
                errors=["Submission must be a list of records."],
            )

        errors: List[str] = []
        expected_map = {_record_key(row): row for row in self._expected_data}

        submitted_map: Dict[str, Dict[str, Any]] = {}
        duplicate_keys = set()
        for row in submitted:
            if not isinstance(row, dict):
                continue
            normalized = _normalize_record(row)
            key = _record_key(normalized)
            if key in submitted_map:
                duplicate_keys.add(key)
            submitted_map[key] = normalized

        expected_keys = set(expected_map.keys())
        submitted_keys = set(submitted_map.keys())
        matched_keys = expected_keys & submitted_keys

        expected_count = len(expected_keys)
        record_matching = (len(matched_keys) / expected_count) if expected_count else 0.0
        completeness = record_matching

        total_fields = self.total_gradable_fields
        correct_fields = 0

        for key, expected in expected_map.items():
            actual = submitted_map.get(key)
            if actual is None:
                if len(errors) < 30:
                    errors.append(f"Missing reconciled record: {key}")
                continue

            for field in _OUTPUT_FIELDS:
                if _field_match(field, expected.get(field), actual.get(field)):
                    correct_fields += 1
                elif len(errors) < 30:
                    errors.append(f"Mismatch for {key} field '{field}'")

        field_correctness = (correct_fields / total_fields) if total_fields else 0.0

        conflict_total = expected_count * len(_CONFLICT_FIELDS)
        conflict_correct = 0
        for key, expected in expected_map.items():
            actual = submitted_map.get(key)
            if actual is None:
                continue
            for field in _CONFLICT_FIELDS:
                if _field_match(field, expected.get(field), actual.get(field)):
                    conflict_correct += 1
        conflict_resolution = (
            conflict_correct / conflict_total if conflict_total else 0.0
        )

        if duplicate_keys and len(errors) < 30:
            errors.append(f"Duplicate reconciled records detected for keys: {sorted(duplicate_keys)[:5]}")

        extra_keys = sorted(submitted_keys - expected_keys)
        if extra_keys and len(errors) < 30:
            errors.append(f"Unexpected extra reconciled records: {extra_keys[:5]}")

        score = (
            0.30 * record_matching
            + 0.30 * field_correctness
            + 0.25 * conflict_resolution
            + 0.15 * completeness
        )
        score = max(0.0, min(1.0, score))

        return GradeResult(
            score=score,
            correct_fields=correct_fields,
            total_fields=total_fields,
            errors=errors,
        )
