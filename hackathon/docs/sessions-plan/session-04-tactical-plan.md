# Session 04 Tactical Plan: Environment Reset/Step Loop and Reward Shaping

Date: 2026-03-29
Session spec: Session 4 (Environment Reset/Step Loop and Reward Shaping)

Inputs read:
- hackathon/docs/sessions/04-session-environment-loop-and-reward.md
- hackathon/docs/WINNING-PLAN.md
- hackathon/docs/PS.md

## 1) Scope and Non-Scope

### In Scope (Session 4 only)
- Implement/reset runtime episode state and transition logic in:
  - `hackathon/data_cleaning_env/server/data_cleaning_environment.py`
- Apply any minimal runtime model adjustments required by environment behavior in:
  - `hackathon/data_cleaning_env/models.py`
- Enforce Session 4 reward shaping:
  - absolute score + improvement - penalties (repeat/stagnation/regression)
  - reward clamped to `[0.0, 1.0]`
- Implement done logic:
  - done when `step_count >= max_steps` or score reaches near-perfect threshold
- Ensure deterministic reset semantics:
  - no loop/stagnation state leakage across episodes

### Out of Scope (deferred)
- Task grader formula changes in:
  - `hackathon/data_cleaning_env/server/tasks/easy.py`
  - `hackathon/data_cleaning_env/server/tasks/medium.py`
  - `hackathon/data_cleaning_env/server/tasks/hard.py`
- Inference, Docker, deployment, and submission packaging work.
- README expansion and baseline score benchmarking.
- Any refactor not directly required to satisfy Session 4 reset/step/reward/done requirements.

## 2) Explicit Environment Plan (Mandatory Step 1)

### 2.1 State Fields Updated on `reset()`
`reset(task_id=...)` must fully reinitialize mutable runtime fields:
- `_task`: selected task from registry by `task_id`
- `_best_score = 0.0`
- `_previous_score = 0.0`
- `_last_action_hash = None`
- `_no_progress_streak = 0`
- `_state = DataCleanState(...)` with:
  - `episode_id`: new ID (or supplied override)
  - `step_count = 0`
  - `task_id`
  - `total_fields`
  - `correct_fields = 0`
  - `max_steps` from task

`reset()` observation contract:
- `current_score = 0.0`
- `done = False`
- `reward = 0.0`
- `validation_errors = []`
- metadata includes at least: `task_id`, `step=0`, `best_score=0.0`, `no_progress_streak=0`

### 2.2 State Fields Updated on `step()`
On each `step(action)`:
- Increment `self._state.step_count` exactly once.
- Grade submitted payload with task grader.
- Update:
  - `self._state.correct_fields`
  - `self._best_score = max(self._best_score, score)`
  - `self._previous_score = score` (after reward computation)
  - loop/stagnation trackers

### 2.3 Reward Components and Exact Formula
Use this exact shape (derived from WINNING-PLAN + Session 4 requirement):

- `score = current absolute task score`
- `improvement = max(0.0, score - previous_score)`
- `regression_term = max(0.0, previous_score - score)`
- `repeat_penalty = 0.15 if action repeats exactly else 0.0`
- `stagnation_penalty = min(0.1 * no_progress_streak, 0.3)`

Raw reward:

`raw_reward = 0.50 * score + 0.25 * improvement - 0.05 * regression_term - repeat_penalty - stagnation_penalty`

Final reward:

`reward = clamp(raw_reward, 0.0, 1.0)`

Notes:
- This satisfies “absolute score + improvement - penalties.”
- Regression penalty coefficient is equivalent to the winning-plan composite when expanded.

### 2.4 Repeat Action and Stagnation Detection Strategy
- Repeat detection:
  - Build deterministic action fingerprint from `action.data` (stable serialization or equivalent canonical ordering).
  - Compare to previous fingerprint.
  - If equal, apply `repeat_penalty`.
- Stagnation detection:
  - If `abs(score - previous_score) < 1e-3`, increment streak.
  - Else reset streak to zero.
  - Apply capped streak penalty (`<= 0.3`).
- Reset behavior:
  - both repeat/stagnation trackers are reset on every `reset()`.

### 2.5 Done Conditions and Metadata Schema
Episode terminates when either condition holds:
- `self._state.step_count >= self._state.max_steps`
- `score >= 0.99` (near-perfect target)

Step metadata schema (minimum tactical contract):
- `task_id: str`
- `step: int`
- `best_score: float`
- `correct_fields: int`
- `total_fields: int`
- `no_progress_streak: int`
- `repeat_action: bool`
- `done_reason: str` one of `in_progress | max_steps | target_score`

## 3) Ordered Implementation Steps with Target Files

1. Confirm precondition artifact exists
- Target: `hackathon/docs/sessions-plan/session-04-tactical-plan.md`
- Gate: plan file saved before any Session 4 code edits.

2. Implement reset lifecycle and state reinitialization
- Target: `hackathon/data_cleaning_env/server/data_cleaning_environment.py`
- Outcomes:
  - clean state reset with no mutable leakage
  - deterministic initial observation

3. Implement step transition accounting
- Target: `hackathon/data_cleaning_env/server/data_cleaning_environment.py`
- Outcomes:
  - exact step increment semantics
  - state score/correctness updates after grading

4. Implement anti-loop reward shaping
- Target: `hackathon/data_cleaning_env/server/data_cleaning_environment.py`
- Outcomes:
  - repeat detection + penalty
  - stagnation detection + capped penalty
  - regression handling
  - reward clamp to `[0,1]`

5. Implement done logic and metadata completeness
- Target: `hackathon/data_cleaning_env/server/data_cleaning_environment.py`
- Outcomes:
  - termination by max steps or near-perfect score
  - metadata keys aligned to Section 2.5

6. Apply minimal model adjustments only if runtime contract requires them
- Target: `hackathon/data_cleaning_env/models.py`
- Outcomes:
  - typed observation/state fields remain consistent with environment output

7. Execute verification suite and collect evidence
- Targets:
  - compile/runtime checks from Session 4
  - tactical checks for loop penalties, reward bounds, done behavior

## 4) Risks and Mitigations

| Risk | Impact | Mitigation | Verification Hook |
|---|---|---|---|
| State leakage across episodes | Non-deterministic trajectories, scoring instability | Explicitly reinitialize `_task`, `_state`, `_best_score`, `_previous_score`, `_last_action_hash`, `_no_progress_streak` in `reset()` | reset -> step loop -> reset assertions |
| Reward outside bounds | Violates OpenEnv expectations and Session 4 check | Clamp reward at final step to `[0.0, 1.0]` | assertion over repeated trajectory rewards |
| Repeat detection misses equivalent payloads | Loop behavior not penalized reliably | Use deterministic canonicalization of action payload before hashing/comparison | repeated identical action test with same structured payload |
| Stagnation penalty too aggressive or never applied | Poor learning signal | Use tolerance-based stagnation (`1e-3`) and cap at `0.3` | monotonic/non-increasing repeated-action reward assertions |
| Done boundary off-by-one | Episodes terminate too early/late | Base done check on post-increment `step_count` and exact threshold conditions | max-step exhaustion check + near-perfect check |
| Metadata drift from tactical contract | Weak observability/debugging | Define fixed metadata keys and done reason conventions | metadata key presence assertions |

## 5) Validation Checklist Mapped to Session 4 Spec

| Session 4 requirement | Tactical check | Pass condition |
|---|---|---|
| Plan first | This tactical plan exists before code edits | file present at required path |
| Plan states state fields on reset/step | Section 2.1 and 2.2 | explicit field-level reset/update contract documented |
| Plan states reward components/formula | Section 2.3 | exact formula and clamp defined |
| Plan states repeat/stagnation strategy | Section 2.4 | explicit detection and penalty rules documented |
| Plan states done conditions and metadata schema | Section 2.5 | both termination conditions + metadata keys documented |
| `reset()` fully resets mutable state | Section 3 step 2 + Section 6 checks | second reset shows clean loop/streak baseline |
| `step()` increments step count correctly | Section 3 step 3 + Section 6 checks | `step_count` increments by one per action |
| Reward uses absolute + improvement - penalties | Section 3 step 4 + Section 6 checks | computed rewards follow formula and clamp |
| Done when max steps or near-perfect score | Section 3 step 5 + Section 6 checks | done asserted under both conditions |
| Repeated identical actions lower reward | Section 6 repeated-action command | reward trend non-increasing under repeated same action |
| Reward remains in `[0,1]` | Section 6 checks | all observed rewards bounded |
| Deliverable evidence includes short trajectory | Section 6 printed outputs | trajectory logs show penalties/progression |
| Deterministic and no state leakage | Section 6 reset/replay checks | same setup produces stable behavior; reset clears trackers |

## 6) Exact Verification Commands and Pass Criteria

Run from repository root unless stated.

### 6.1 Required Session 4 Commands (verbatim)

```bash
cd hackathon
python -m compileall data_cleaning_env/
python - <<'PY'
from data_cleaning_env.server.data_cleaning_environment import DataCleanEnvironment
from data_cleaning_env.models import DataCleanAction
from data_cleaning_env.server.tasks import TASK_REGISTRY

env = DataCleanEnvironment()
obs = env.reset(task_id="easy")
print("reset_ok", obs.current_score, obs.done)

# Use partial expected data to get a non-zero baseline score
task = TASK_REGISTRY["easy"]
expected = getattr(task, "_expected_data", getattr(task, "expected_data", []))
partial = expected[: max(1, len(expected) // 3)]

for i in range(3):
    out = env.step(DataCleanAction(data=partial))
    print("step", i + 1, "score", out.current_score, "reward", out.reward, "done", out.done)

obs2 = env.reset(task_id="easy")
print("reset_again", obs2.current_score, obs2.done)
PY
```

Pass criteria for required commands:
- Compile succeeds with no syntax errors.
- First reset prints score `0.0` and `done=False`.
- Step 1 shows a non-zero reward (partial credit). Steps 2-3 show lower rewards (repeat/stagnation penalties).
- Second reset again prints score `0.0` and `done=False`.

### 6.2 Tactical Supplement Checks (must also pass)

```bash
cd hackathon
python - <<'PY'
from data_cleaning_env.server.data_cleaning_environment import DataCleanEnvironment
from data_cleaning_env.models import DataCleanAction
from data_cleaning_env.server.tasks import TASK_REGISTRY

# A) Repeat-action penalties and reward bounds
#    Use partial expected data so score is non-zero, making penalties visible.
env = DataCleanEnvironment()
obs = env.reset(task_id="easy")
assert obs.current_score == 0.0 and obs.done is False and obs.reward == 0.0
task = TASK_REGISTRY["easy"]
expected = getattr(task, "_expected_data", getattr(task, "expected_data", []))
partial = expected[: max(1, len(expected) // 3)]
rewards = []
for _ in range(3):
    out = env.step(DataCleanAction(data=partial))
    rewards.append(float(out.reward))
assert all(0.0 <= r <= 1.0 for r in rewards), f"bounds: {rewards}"
assert rewards[1] < rewards[0], f"repeat not penalized: {rewards}"
assert rewards[2] <= rewards[1], f"stagnation not penalized: {rewards}"

# B) Reset clears loop/stagnation state
obs2 = env.reset(task_id="easy")
assert obs2.current_score == 0.0 and obs2.done is False and obs2.reward == 0.0

# C) Done at max steps
env = DataCleanEnvironment()
env.reset(task_id="easy")
for _ in range(env.state.max_steps):
    out = env.step(DataCleanAction(data=[]))
assert out.done is True
assert env.state.step_count == env.state.max_steps

# D) Done at near-perfect score
env = DataCleanEnvironment()
env.reset(task_id="easy")
task = TASK_REGISTRY["easy"]
expected = getattr(task, "_expected_data", getattr(task, "expected_data", []))
out = env.step(DataCleanAction(data=expected))
assert out.current_score >= 0.99
assert out.done is True

print("session4_tactical_checks_ok")
PY
```

Pass criteria for tactical supplement checks:
- Rewards remain within `[0.0, 1.0]`.
- Repeated identical actions produce non-increasing rewards across consecutive repeats.
- Post-reset baseline is clean (`current_score=0`, `reward=0`, `done=False`).
- Max-step path terminates exactly at configured step budget.
- Near-perfect submission path terminates immediately (`done=True` with score `>= 0.99`).
- Script prints `session4_tactical_checks_ok`.

## 7) Go / No-Go Decision

### Go Conditions
- This tactical plan exists at the mandatory output path.
- Scope is limited to Session 4 files and requirements.
- All Section 6 checks pass after implementation.

### No-Go Conditions
- Any missing reset-state reinitialization causing leakage.
- Any reward formula divergence from Section 2.3.
- Any reward outside `[0,1]`.
- Missing done handling for either max steps or near-perfect score.
- Any implementation spillover into out-of-scope areas before Session 4 gates pass.

### Current Decision
- Go for Session 4 implementation after this plan is accepted.

## 8) Framework-Specific Consultation Notes
- No `ref-repos/OpenEnv` files were consulted for this plan-only Session 4 step.
- If framework behavior ambiguity appears during implementation, consult only minimal relevant paths under `ref-repos/OpenEnv` and record exact file paths in the implementation report.
