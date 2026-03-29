# Session 03 Tactical Plan: Graders and Scoring Determinism

Date: 2026-03-29
Session spec: Session 3 (Graders and Scoring Determinism)

Inputs read:
- hackathon/docs/sessions/03-session-graders-and-scoring-tests.md
- hackathon/docs/WINNING-PLAN.md
- hackathon/docs/PS.md

## 1) Scope and Non-Scope

### In Scope (Session 3 only)
- Implement shared grader utilities and grading entrypoint in:
  - `hackathon/data_cleaning_env/server/graders.py`
- Complete and harden deterministic `grade()` behavior in:
  - `hackathon/data_cleaning_env/server/tasks/easy.py`
  - `hackathon/data_cleaning_env/server/tasks/medium.py`
  - `hackathon/data_cleaning_env/server/tasks/hard.py`
- Add Session 3 scoring and determinism tests in:
  - `hackathon/data_cleaning_env/tests/test_graders.py`
  - `hackathon/data_cleaning_env/tests/test_task_scores.py`
- Enforce score clamping to `[0.0, 1.0]`, deterministic replay behavior, and non-constant score spread.
- Produce score spread evidence for low/medium/high quality submissions.

### Out of Scope (deferred)
- Environment loop/reward shaping changes in `server/data_cleaning_environment.py` (Session 4 concern).
- Inference script, Docker runtime tuning, and deployment validation work.
- README expansion, submission packaging, and non-grading refactors.
- Any edits outside Session 3 target files unless required to fix direct Session 3 blockers.

## 2) Exact Scoring Formulas by Task

Use these formulas exactly, then clamp final score to `[0.0, 1.0]`.

### Easy (`easy.py`)
- Formula:
  - `score = correct_fields / total_fields`
- Definitions:
  - `correct_fields`: number of matching fields across expected records after normalization and keyed alignment.
  - `total_fields`: `len(expected_records) * 8` (8 fixed fields).

### Medium (`medium.py`)
- Formula:
  - `score = 0.2 * schema_compliance + 0.5 * field_accuracy + 0.3 * constraint_satisfaction`
- Definitions:
  - `schema_compliance`: `1.0` only when all expected transformed records are present and output schema/types are valid, else `0.0`.
  - `field_accuracy`: `correct_fields / total_fields` over transformed output fields.
  - `constraint_satisfaction`: passed business constraints fraction.

### Hard (`hard.py`)
- Formula:
  - `score = 0.30 * record_matching + 0.30 * field_correctness + 0.25 * conflict_resolution + 0.15 * completeness`
- Definitions:
  - `record_matching`: fraction of expected reconciled entities matched by deterministic record key.
  - `field_correctness`: field-level correctness ratio across all expected reconciled records.
  - `conflict_resolution`: correctness ratio on conflict-priority fields only.
  - `completeness`: expected reconciled entity coverage ratio.

## 3) Normalization Rules (Deterministic)

Apply deterministic normalization before comparisons.

- String normalization:
  - `strip()`, lowercase, collapse repeated whitespace.
  - Treat null-like tokens (`n/a`, `na`, `null`, `none`, `-`, `--`) as empty string when field semantics allow.
- Numeric normalization:
  - Remove `$` and `,`, parse as float.
  - Numeric comparison tolerance:
    - absolute difference `<= 1.0`
    - relative error `<= 0.01` (1%) for non-zero expected values
    - for zero expected values, absolute check `<= 0.01`
- Date normalization:
  - Parse known date formats and convert to ISO (`YYYY-MM-DD`).
- Phone normalization:
  - Keep digits only; when 10+ digits, use trailing 10 digits and render `XXX-XXX-XXXX`.
- Tags/list normalization:
  - lowercase, trim, deduplicate, sort stable.
- Integer normalization:
  - Parse via deterministic integer conversion for integer-typed fields (for example quantity).

## 4) `validation_errors` Reporting Format

Use deterministic, code-prefixed, stable-format messages in `GradeResult.errors` so observation `validation_errors` are consistent across replays.

- Error message template family:
  - `MISSING_RECORD|key=<record_key>`
  - `MISMATCH|key=<record_key>|field=<field_name>|expected=<normalized_expected>|actual=<normalized_actual>`
  - `DUPLICATE_RECORD|key=<record_key>`
  - `EXTRA_RECORD|key=<record_key>`
  - `SCHEMA_ERROR|record=<record_id_or_index>|detail=<reason>`
- Ordering and truncation:
  - Emit in deterministic key/field order.
  - Cap collected errors per grade call (easy: 25, medium/hard: 30) to keep payload bounded.

## 5) Test Matrix (Mandatory)

Apply this matrix to each task (`easy`, `medium`, `hard`).

| Case | Submission shape | Expected behavior |
|---|---|---|
| Perfect | canonical expected/gold payload | score near 1.0 (`>= 0.95`) |
| Empty | `[]` | score near 0 (`<= 0.05`) |
| Partial | deterministic subset of expected payload | score strictly between empty and perfect |
| Malformed | non-list, wrong schema, invalid record objects | score low (typically 0), deterministic error messages |
| Deterministic replay | same payload graded repeatedly | identical score and identical ordered errors |

Spread requirement for each task:
- `low < medium < high` must hold for representative low/partial/perfect submissions.

## 6) Ordered Implementation Steps with Target Files

1. Confirm planning precondition
- Target file: `hackathon/docs/sessions-plan/session-03-tactical-plan.md`
- Gate: this artifact exists before any Session 3 code edits.

2. Add shared grading utilities and entrypoint
- Target file: `hackathon/data_cleaning_env/server/graders.py`
- Implement:
  - `GradeResult` re-export/compat wrapper if needed.
  - score clamp helper.
  - type-aware field comparison helpers.
  - deterministic normalization helpers used by tasks.
  - `grade_submission(task, submitted_data)` delegator.

3. Complete easy task grading behavior
- Target file: `hackathon/data_cleaning_env/server/tasks/easy.py`
- Ensure:
  - formula is exactly `correct_fields / total_fields`.
  - normalized key matching and stable error ordering.
  - strict clamp and deterministic behavior.

4. Complete medium task grading behavior
- Target file: `hackathon/data_cleaning_env/server/tasks/medium.py`
- Ensure:
  - exact weighted formula and component computation.
  - numeric/date/string tolerance rules align with Section 3.
  - deterministic schema and constraint checks.

5. Complete hard task grading behavior
- Target file: `hackathon/data_cleaning_env/server/tasks/hard.py`
- Ensure:
  - exact weighted formula and conflict-field handling.
  - deterministic reconciliation keying and completeness logic.
  - deterministic duplicate/extra/mismatch reporting.

6. Add scorer and determinism tests
- Target files:
  - `hackathon/data_cleaning_env/tests/test_graders.py`
  - `hackathon/data_cleaning_env/tests/test_task_scores.py`
- Add tests for:
  - clamp bounds, normalization parity, numeric tolerance, and error format.
  - perfect/empty/partial/malformed/replay matrix per task.
  - non-constant spread assertions.

7. Execute verification command suite
- Run all commands in Section 9.
- Record outputs needed for Session 3 deliverables.

8. Gate decision
- If all pass criteria hold, mark Session 3 as GO for closeout.
- If any criterion fails, remain NO-GO and fix only within Session 3 scope.

## 7) Risks and Mitigations

| Risk | Impact | Mitigation | Verification Hook |
|---|---|---|---|
| Formula drift from winning plan | Incorrect grader behavior and scoring ambiguity | Keep explicit formulas in code comments/tests and assert component math in tests | component-level tests in `test_task_scores.py` |
| Nondeterministic error ordering | Replay instability | Sort keys/fields before diffing; stable error template format | replay assertions on errors list equality |
| Numeric tolerance mismatch across tasks | Inconsistent grading fairness | Centralize numeric compare helper in `server/graders.py` and reuse | unit tests in `test_graders.py` |
| Missing clamp edge handling | Score out of range | Clamp in each task result path and test bounds | bound assertions over multiple submission variants |
| Key collision for record matching | False match/mismatch counts | deterministic key fallback order (email -> phone -> name+secondary anchor) | keying tests + mismatch diagnostics |
| Hidden constant-score regressions | DQ risk | enforce low/partial/perfect spread checks for each task | spread check script in Section 9 |

## 8) Validation Checklist Mapped to Session 3 Spec

| Session 3 requirement | Tactical check | Pass condition |
|---|---|---|
| Plan first | This file exists before code edits | `session-03-tactical-plan.md` present |
| Include exact scoring formulas by task | Section 2 | formulas match easy/medium/hard definitions exactly |
| Include normalization rules | Section 3 | rules are explicit and testable |
| Include `validation_errors` format | Section 4 | deterministic code-prefixed format defined |
| Include test matrix | Section 5 | perfect/empty/partial/malformed/replay covered |
| Implement `server/graders.py` and complete task `grade()` methods | Section 6 steps 2-5 | files updated with deterministic logic |
| Add recommended tests | Section 6 step 6 | both test files created and passing |
| Scores clamped to `[0,1]` | Sections 2/6/9 | all observed scores within bounds |
| Deterministic output for identical input | Sections 5/9 | replay check exact equality passes |
| Distinct low/medium/high outputs | Sections 5/9 | strict score spread per task passes |
| Verify using required commands | Section 9 | all commands exit successfully and meet criteria |
| Done criteria: no formula ambiguity | Sections 2 and 9 | formulas explicit and all checks pass |

## 9) Exact Verification Commands and Pass Criteria

Run from repository root unless stated.

```bash
cd hackathon/data_cleaning_env

# Session 3 required checks
python -m compileall .
pytest -q
python - <<'PY'
from server.tasks import TASK_REGISTRY

def show(task):
    perfect_payload = getattr(task, "_expected_data", getattr(task, "expected_data", getattr(task, "gold_data", [])))
    empty = task.grade([]).score
    perfect = task.grade(perfect_payload).score
    print(task.task_id, "empty=", empty, "perfect=", perfect)

for t in TASK_REGISTRY.values():
    show(t)
PY

# Tactical deterministic replay + spread checks
python - <<'PY'
from server.tasks import TASK_REGISTRY

for task in TASK_REGISTRY.values():
    gold = getattr(task, "_expected_data", getattr(task, "expected_data", getattr(task, "gold_data", [])))
    partial = gold[: max(1, len(gold) // 2)] if isinstance(gold, list) else []

    empty_result = task.grade([])
    partial_result = task.grade(partial)
    perfect_result = task.grade(gold)
    replay_result = task.grade(partial)
    malformed_result = task.grade([{"bad": "shape"}])

    print(
        task.task_id,
        "empty=", round(empty_result.score, 6),
        "malformed=", round(malformed_result.score, 6),
        "partial=", round(partial_result.score, 6),
        "perfect=", round(perfect_result.score, 6),
        "replay_equal=", partial_result.score == replay_result.score,
    )

    assert 0.0 <= empty_result.score <= 1.0
    assert 0.0 <= partial_result.score <= 1.0
    assert 0.0 <= perfect_result.score <= 1.0
    assert empty_result.score <= 0.05
    assert perfect_result.score >= 0.95
    assert empty_result.score < partial_result.score < perfect_result.score
    assert partial_result.score == replay_result.score
    assert partial_result.errors == replay_result.errors

print("session3_spread_and_determinism_ok")
PY
```

### Pass Criteria
- `python -m compileall .` completes with no syntax errors.
- `pytest -q` passes all Session 3 grader/scoring tests.
- For every task: empty score is near 0 (`<= 0.05`), perfect score is near 1 (`>= 0.95`).
- For every task: low/partial/perfect produce distinct ordered scores (`low < partial < perfect`).
- Deterministic replay check passes: identical score and identical ordered `errors` for identical input.
- All printed scores are in `[0.0, 1.0]`.

## 10) Go / No-Go Decision

### Go Conditions
- This tactical plan is present and accepted.
- Session 3 implementation is limited to scoped files in Section 1.
- All verification commands in Section 9 pass with listed criteria.

### No-Go Conditions
- Any formula divergence from Section 2.
- Any non-deterministic replay result (score or error ordering differs).
- Any constant-score behavior across low/partial/perfect cases.
- Any requested change outside Session 3 scope before Session 3 gates pass.

### Current Decision
- Go for Session 3 implementation once this plan is approved.

## 11) Framework-Specific Consultation Notes

- No `ref-repos/OpenEnv` files were consulted for this plan-only Session 3 step.
- If framework ambiguity appears during Session 3 implementation, consult only minimal relevant paths in `ref-repos/OpenEnv` and record exact file paths in the implementation report.