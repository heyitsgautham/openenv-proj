# Session 2: Task Framework and Dataset Ground Truth

Estimated effort: 3-4 hours

## Goal
Implement deterministic task definitions and all task data files for easy, medium, and hard tasks.

## Inputs
- Session 1 output
- hackathon/docs/WINNING-PLAN.md (Task specs and formulas)

## Tactical Plan Output (Plan Prompt Artifact)
- hackathon/docs/sessions-plan/session-02-tactical-plan.md

## Mandatory Workflow
1. Plan first.
2. Save the tactical plan to the Tactical Plan Output file.
3. Implement/execute using both this session spec and the tactical plan.
4. Verify against checks from both this session spec and the tactical plan.
5. Report artifacts and blockers.

## Step 1: Plan First
Write a concise plan covering:
- Data schema per task and required fields.
- JSON file naming and loading approach.
- Determinism strategy (no random mutation unless seed-controlled).
- Record counts and expected overlap for hard task.

Do not implement until plan is complete.
The plan must be saved to the Tactical Plan Output file.

## Step 2: Implement and Execute
Implement:

- hackathon/data_cleaning_env/server/tasks/easy.py
- hackathon/data_cleaning_env/server/tasks/medium.py
- hackathon/data_cleaning_env/server/tasks/hard.py
- Update hackathon/data_cleaning_env/server/tasks/__init__.py with TASK_REGISTRY.

Create data files:

Precondition: Tactical Plan Output file exists.

- easy_input.json, easy_expected.json
- medium_input.json, medium_rules.json, medium_reference.json, medium_expected.json
- hard_source_a.json, hard_source_b.json, hard_source_c.json, hard_spec.json, hard_expected.json

Implementation notes:
- Keep task metadata explicit: task_id, description, max_steps, total_gradable_fields.
- Ensure file loading paths are stable when run from package root.
- Keep data sizes bounded per WINNING-PLAN constraints.

## Step 3: Verify
Run:

```bash
cd hackathon/data_cleaning_env
python -m compileall .
python - <<'PY'
from server.tasks import TASK_REGISTRY
for k, t in TASK_REGISTRY.items():
    print(k, t.max_steps, len(t.input_data), t.total_gradable_fields)
PY
```

Verification must confirm:
- All three tasks load without file errors.
- task_id keys are exactly easy, medium, hard.
- max_steps are 10, 15, 20.
- All checks defined in the tactical plan are completed.

## Deliverables
- Three task classes.
- Full data asset set under server/tasks/data.
- Deterministic load summary.

## Done Criteria
- TASK_REGISTRY loads cleanly.
- All JSON resources parse and map to task objects.
- No missing file/path ambiguity.
