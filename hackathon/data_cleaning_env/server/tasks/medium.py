"""Medium task definition for deterministic business rule transformations."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from ..graders import (
    append_error,
    clamp_score,
    normalize_date,
    normalize_string,
    numeric_match,
    parse_float,
    parse_int,
)
from .base import BaseTask, GradeResult

_DATA_DIR = Path(__file__).resolve().parent / "data"
_OUTPUT_FIELDS = [
    "transaction_id",
    "full_name",
    "email",
    "street",
    "city",
    "state",
    "zip",
    "region",
    "amount_usd",
    "tax",
    "total",
    "tier",
    "start_date",
    "end_date",
    "quantity",
]
_NUMERIC_FIELDS = {"amount_usd", "tax", "total"}
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


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
    return normalize_string(value, null_tokens=())


def _norm_date(value: Any) -> str:
    return normalize_date(value)


def _to_float(value: Any) -> float | None:
    return parse_float(value)


def _to_int(value: Any) -> int | None:
    return parse_int(value)


def _normalize_record(row: Dict[str, Any]) -> Dict[str, Any]:
    amount_usd = _to_float(row.get("amount_usd"))
    tax = _to_float(row.get("tax"))
    total = _to_float(row.get("total"))

    return {
        "transaction_id": _norm_text(row.get("transaction_id")),
        "full_name": _norm_text(row.get("full_name")),
        "email": _norm_text(row.get("email")),
        "street": _norm_text(row.get("street")),
        "city": _norm_text(row.get("city")),
        "state": _norm_text(row.get("state")),
        "zip": _norm_text(row.get("zip")),
        "region": _norm_text(row.get("region")),
        "amount_usd": round(amount_usd, 2) if amount_usd is not None else None,
        "tax": round(tax, 2) if tax is not None else None,
        "total": round(total, 2) if total is not None else None,
        "tier": _norm_text(row.get("tier")),
        "start_date": _norm_date(row.get("start_date")),
        "end_date": _norm_date(row.get("end_date")),
        "quantity": _to_int(row.get("quantity")),
    }


def _numeric_match(expected: Any, actual: Any) -> bool:
    return numeric_match(expected, actual)


def _is_end_after_start(start_date: str, end_date: str) -> bool:
    if not start_date or not end_date:
        return False
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        return False
    return end_dt > start_dt


class MediumTask(BaseTask):
    """Business transformation task with weighted composite grading."""

    def __init__(self) -> None:
        self.task_id = "medium"
        self.description = (
            "Transform raw transaction data using explicit business rules, reference tables, and constraints."
        )
        self.max_steps = 15

        input_data = _load_json("medium_input.json")
        rules = _load_json("medium_rules.json")
        reference = _load_json("medium_reference.json")
        expected_data = _load_json("medium_expected.json")

        if not isinstance(input_data, list):
            raise ValueError("medium_input.json must contain a list of records")
        if not isinstance(rules, dict):
            raise ValueError("medium_rules.json must contain an object")
        if not isinstance(reference, dict):
            raise ValueError("medium_reference.json must contain an object")
        if not isinstance(expected_data, list):
            raise ValueError("medium_expected.json must contain a list of records")

        self.input_data = input_data
        self.rules = rules
        self.reference = reference
        self._expected_data = [_normalize_record(row) for row in expected_data]
        self.expected_data = self._expected_data
        self.gold_data = self._expected_data
        self.target_schema = {
            "transaction_id": "string",
            "full_name": "string",
            "email": "string",
            "street": "string",
            "city": "string",
            "state": "string",
            "zip": "string",
            "region": "string",
            "amount_usd": "number",
            "tax": "number",
            "total": "number",
            "tier": "string",
            "start_date": "date",
            "end_date": "date",
            "quantity": "integer",
        }
        self.total_gradable_fields = len(self._expected_data) * len(_OUTPUT_FIELDS)

    def _schema_compliance(self, submitted_map: Dict[str, Dict[str, Any]]) -> float:
        expected_ids = {row["transaction_id"] for row in self._expected_data}
        if not expected_ids.issubset(set(submitted_map.keys())):
            return 0.0

        for tx_id in expected_ids:
            row = submitted_map[tx_id]
            if not all(field in row for field in _OUTPUT_FIELDS):
                return 0.0
            if row.get("transaction_id") != tx_id:
                return 0.0
            if any(_to_float(row.get(field)) is None for field in _NUMERIC_FIELDS):
                return 0.0
            if _to_int(row.get("quantity")) is None:
                return 0.0
            if not _norm_date(row.get("start_date")) or not _norm_date(row.get("end_date")):
                return 0.0
        return 1.0

    def grade(self, submitted: List[Dict[str, Any]]) -> GradeResult:
        max_errors = 30
        if not isinstance(submitted, list):
            return GradeResult(
                score=0.0,
                correct_fields=0,
                total_fields=self.total_gradable_fields,
                errors=["SCHEMA_ERROR|detail=submission_must_be_list|record=root"],
            )

        errors: List[str] = []
        expected_map = {row["transaction_id"]: row for row in self._expected_data}

        submitted_map: Dict[str, Dict[str, Any]] = {}
        duplicate_ids = set()
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
            normalized = _normalize_record(row)
            tx_id = normalized.get("transaction_id", "")
            if not tx_id:
                append_error(
                    errors,
                    max_errors,
                    "SCHEMA_ERROR",
                    detail="missing_transaction_id",
                    record=index,
                )
                continue
            if tx_id in submitted_map:
                duplicate_ids.add(tx_id)
            submitted_map[tx_id] = normalized

        schema_compliance = self._schema_compliance(submitted_map)

        correct_fields = 0
        total_fields = self.total_gradable_fields

        for tx_id in sorted(expected_map):
            expected = expected_map[tx_id]
            actual = submitted_map.get(tx_id)
            if actual is None:
                append_error(errors, max_errors, "MISSING_RECORD", key=tx_id)
                continue

            for field in _OUTPUT_FIELDS:
                expected_value = expected.get(field)
                actual_value = actual.get(field)

                if field in _NUMERIC_FIELDS:
                    matches = _numeric_match(expected_value, actual_value)
                elif field == "quantity":
                    matches = _to_int(expected_value) == _to_int(actual_value)
                elif field in {"start_date", "end_date"}:
                    matches = _norm_date(expected_value) == _norm_date(actual_value)
                else:
                    matches = _norm_text(expected_value) == _norm_text(actual_value)

                if matches:
                    correct_fields += 1
                else:
                    append_error(
                        errors,
                        max_errors,
                        "MISMATCH",
                        actual=actual_value,
                        expected=expected_value,
                        field=field,
                        key=tx_id,
                    )

        field_accuracy = (correct_fields / total_fields) if total_fields else 0.0

        constraints_total = len(self._expected_data) * 3
        constraints_passed = 0
        for tx_id in sorted(expected_map):
            actual = submitted_map.get(tx_id)
            if actual is None:
                continue

            start_date = _norm_date(actual.get("start_date"))
            end_date = _norm_date(actual.get("end_date"))
            if _is_end_after_start(start_date, end_date):
                constraints_passed += 1

            if _EMAIL_RE.match(_norm_text(actual.get("email"))):
                constraints_passed += 1

            quantity = _to_int(actual.get("quantity"))
            if quantity is not None and quantity > 0:
                constraints_passed += 1

        constraint_satisfaction = (
            constraints_passed / constraints_total if constraints_total else 0.0
        )

        for tx_id in sorted(duplicate_ids):
            append_error(errors, max_errors, "DUPLICATE_RECORD", key=tx_id)

        for tx_id in sorted(set(submitted_map.keys()) - set(expected_map.keys())):
            append_error(errors, max_errors, "EXTRA_RECORD", key=tx_id)

        score = (
            0.2 * schema_compliance
            + 0.5 * field_accuracy
            + 0.3 * constraint_satisfaction
        )
        score = clamp_score(score)

        return GradeResult(
            score=score,
            correct_fields=correct_fields,
            total_fields=total_fields,
            errors=errors,
        )
