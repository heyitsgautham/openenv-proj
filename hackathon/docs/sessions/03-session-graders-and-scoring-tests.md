# Session 3: Graders and Scoring Determinism

Estimated effort: 3-4 hours

## Goal
Implement full grading logic and prove deterministic, non-constant scoring behavior across all tasks.

## Inputs
- Session 2 output
- hackathon/docs/WINNING-PLAN.md (grading formulas)

## Tactical Plan Output (Plan Prompt Artifact)
- hackathon/docs/sessions-plan/session-03-tactical-plan.md

## Mandatory Workflow
1. Plan first.
2. Save the tactical plan to the Tactical Plan Output file.
3. Implement/execute using both this session spec and the tactical plan.
4. Verify against checks from both this session spec and the tactical plan.
5. Report artifacts and blockers.

## Step 1: Plan First
Plan should include:
- Exact scoring formulas by task.
- Normalization rules (numeric tolerance, string normalization).
- Error reporting format for validation_errors.
- Test matrix: perfect, empty, partial, malformed, deterministic replay.

Do not implement before plan is written.
The plan must be saved to the Tactical Plan Output file.

## Step 2: Implement and Execute
Implement:

- hackathon/data_cleaning_env/server/graders.py
- Complete grade() in easy.py, medium.py, hard.py

Add tests (recommended):

Precondition: Tactical Plan Output file exists.

- hackathon/data_cleaning_env/tests/test_graders.py
- hackathon/data_cleaning_env/tests/test_task_scores.py

Implementation requirements:
- All scores clamped to [0.0, 1.0].
- Deterministic output for identical input.
- Distinct outputs for low/medium/high quality submissions.

## Step 3: Verify
Run:

```bash
cd hackathon/data_cleaning_env
python -m compileall .
pytest -q
python - <<'PY'
from server.tasks import TASK_REGISTRY

def show(task):
    empty = task.grade([]).score
    perfect = task.grade(getattr(task, "expected_data", getattr(task, "gold_data", []))).score
    print(task.task_id, "empty=", empty, "perfect=", perfect)

for t in TASK_REGISTRY.values():
    show(t)
PY
```

Verification must confirm:
- Empty input gives near 0.
- Perfect input gives near 1.
- Replay of same submission gives same score.
- All checks defined in the tactical plan are completed.

## Deliverables
- Complete graders.
- Test suite evidence.
- Score spread summary table.

## Done Criteria
- Non-constant score behavior is demonstrated.
- Determinism is proven.
- No formula ambiguity remains.
