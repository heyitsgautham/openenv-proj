# Session 4: Environment Reset/Step Loop and Reward Shaping

Estimated effort: 2-3 hours

## Goal
Implement DataCleanEnvironment with clean resets, step transitions, done logic, and anti-loop reward shaping.

## Inputs
- Session 3 output
- hackathon/docs/WINNING-PLAN.md (reward design and penalties)

## Tactical Plan Output (Plan Prompt Artifact)
- hackathon/docs/sessions-plan/session-04-tactical-plan.md

## Mandatory Workflow
1. Plan first.
2. Save the tactical plan to the Tactical Plan Output file.
3. Implement/execute using both this session spec and the tactical plan.
4. Verify against checks from both this session spec and the tactical plan.
5. Report artifacts and blockers.

## Step 1: Plan First
Plan should state:
- State fields updated on reset/step.
- Reward components and exact formula.
- Repeat action and stagnation detection strategy.
- Done conditions and metadata schema.

Do not implement until plan is explicit.
The plan must be saved to the Tactical Plan Output file.

## Step 2: Implement and Execute
Implement:

Precondition: Tactical Plan Output file exists.

- hackathon/data_cleaning_env/server/data_cleaning_environment.py
- Any model adjustments required by runtime behavior

Requirements:
- reset() fully resets mutable state.
- step() increments step_count correctly.
- Reward uses absolute score + improvement - penalties.
- done when max_steps reached or near-perfect score reached.

## Step 3: Verify
Run:

```bash
cd hackathon/data_cleaning_env
python -m compileall .
python - <<'PY'
from data_cleaning_env.server.data_cleaning_environment import DataCleanEnvironment
from data_cleaning_env.models import DataCleanAction

env = DataCleanEnvironment()
obs = env.reset(task_id="easy")
print("reset_ok", obs.current_score, obs.done)

same = [{"x": 1}]
for i in range(3):
    out = env.step(DataCleanAction(data=same))
    print("step", i + 1, "score", out.current_score, "reward", out.reward, "done", out.done)

obs2 = env.reset(task_id="easy")
print("reset_again", obs2.current_score, obs2.done)
PY
```

Verification must confirm:
- reset clears prior streak/loop state.
- repeated identical actions trigger lower rewards over steps.
- reward remains in [0, 1].
- All checks defined in the tactical plan are completed.

## Deliverables
- Working environment class.
- Short trajectory evidence showing penalties and progression.

## Done Criteria
- Environment behaves deterministically and safely.
- No state leakage across episodes.
