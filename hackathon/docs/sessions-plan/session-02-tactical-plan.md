# Session 02 Tactical Plan: Task Framework and Dataset Ground Truth

Date: 2026-03-29
Session spec: Session 2 (Task Framework and Dataset Ground Truth)

## 1) Scope and Non-Scope

### In Scope (Session 2 only)
- Implement deterministic task definitions in:
  - `hackathon/data_cleaning_env/server/tasks/easy.py`
  - `hackathon/data_cleaning_env/server/tasks/medium.py`
  - `hackathon/data_cleaning_env/server/tasks/hard.py`
- Update `hackathon/data_cleaning_env/server/tasks/__init__.py` with final `TASK_REGISTRY` keys: `easy`, `medium`, `hard`.
- Create all required JSON task assets in `hackathon/data_cleaning_env/server/tasks/data/`:
  - `easy_input.json`, `easy_expected.json`
  - `medium_input.json`, `medium_rules.json`, `medium_reference.json`, `medium_expected.json`
  - `hard_source_a.json`, `hard_source_b.json`, `hard_source_c.json`, `hard_spec.json`, `hard_expected.json`
- Keep task metadata explicit in each task class: `task_id`, `description`, `max_steps`, `total_gradable_fields`.
- Ensure deterministic, package-root-stable JSON loading.
- Run session-mandated and tactical verification checks.

### Out of Scope (deferred)
- Environment `reset`/`step` behavior changes outside task data/task class wiring.
- Inference script work, Docker/runtime deployment work, and Hugging Face Space deployment.
- README expansion and submission packaging.
- Refactors in unrelated modules or repositories.

## 2) Data Schema and Dataset Contract (Plan First)

This section satisfies Session 2 Step 1 requirements: schema, naming/loading strategy, determinism, and hard-task record overlap targets.

### Easy Task Contract
- Goal: basic deterministic cleaning with exact field-level grading.
- Files:
  - `easy_input.json`: exactly 50 messy records.
  - `easy_expected.json`: canonical cleaned records (deduplicated target set).
- Required output fields (8):
  - `name`, `email`, `phone`, `date_of_birth`, `status`, `amount`, `category`, `notes`
- Planned issues in input:
  - Missing/null-like values, type formatting errors, mixed case/whitespace, and exact duplicates.
- `max_steps`: 10.

### Medium Task Contract
- Goal: deterministic business-rule transformation over transaction-like records.
- Files:
  - `medium_input.json`: exactly 100 raw records.
  - `medium_rules.json`: transformation and validation rules.
  - `medium_reference.json`: reference tables (tax rates, currency rates).
  - `medium_expected.json`: canonical transformed output.
- Required input fields:
  - `transaction_id`, `first_name`, `last_name`, `email`, `address`, `region`, `currency`, `amount`, `start_date`, `end_date`, `quantity`
- Required transformed output fields:
  - `transaction_id`, `full_name`, `email`, `street`, `city`, `state`, `zip`, `region`, `amount_usd`, `tax`, `total`, `tier`, `start_date`, `end_date`, `quantity`
- Scoring components follow winning-plan formula:
  - `0.2 * schema_compliance + 0.5 * field_accuracy + 0.3 * constraint_satisfaction`
- `max_steps`: 15.

### Hard Task Contract
- Goal: deterministic multi-source reconciliation with conflict-resolution rules.
- Files:
  - `hard_source_a.json`: 50 records.
  - `hard_source_b.json`: 45 records.
  - `hard_source_c.json`: 40 records.
  - `hard_spec.json`: source priority + exception rules.
  - `hard_expected.json`: golden reconciled records.
- Required source fields (all sources include common matching anchors, plus source-specific attributes):
  - Common anchors: `name`, `email`, `phone`, `address`, `city`, `state`, `postal_code`
  - Source A (financial authority): `lifetime_value`, `last_payment_date`
  - Source B (contact authority): `preferred_channel`, `contact_status`
  - Source C (metadata authority): `created_at`, `tags`
- Required reconciled output fields:
  - `entity_name`, `email`, `phone`, `address`, `city`, `state`, `postal_code`, `lifetime_value`, `contact_status`, `metadata_tags`
- Overlap target:
  - Expected overlap across at least two sources: about 30 entities (target validation band: 28-32).
- Scoring components follow winning-plan formula:
  - `0.30 * record_matching + 0.30 * field_correctness + 0.25 * conflict_resolution + 0.15 * completeness`
- `max_steps`: 20.

## 3) JSON Naming and Loading Approach

- Keep all assets under one fixed directory:
  - `hackathon/data_cleaning_env/server/tasks/data/`
- In each task module (`easy.py`, `medium.py`, `hard.py`), load data via deterministic absolute path resolution from module location:
  - `Path(__file__).resolve().parent / "data" / <filename>`
- Load with UTF-8 and `json.load` only (no runtime mutation of loaded source data).
- Fail fast with explicit filename in exception if a JSON file is missing or malformed.
- Keep stable ordering assumptions for grading by normalizing records before comparison:
  - sort by deterministic key (`transaction_id` or canonical entity key derived from fields).

## 4) Determinism Strategy

- No random mutation in task initialization or grading.
- If any synthetic generation helper is used during data creation, it must be run once offline with a fixed seed and committed as static JSON.
- Graders must be pure functions of input submission and static expected data.
- Normalize comparisons deterministically:
  - strings: trim + lowercase where appropriate
  - numeric values: fixed rounding/tolerance policy
  - dates: ISO normalization before comparison
- Clamp final scores to `[0.0, 1.0]` and keep formulas exactly as defined.
- Compute and store `total_gradable_fields` deterministically from canonical expected outputs.

## 5) Ordered Implementation Steps with Target Files

1. Confirm tactical-plan precondition exists
- Target file: `hackathon/docs/sessions-plan/session-02-tactical-plan.md`
- Result needed before coding: this file present and approved for execution.

2. Create all Session 2 JSON assets
- Target directory: `hackathon/data_cleaning_env/server/tasks/data/`
- Target files:
  - `easy_input.json`, `easy_expected.json`
  - `medium_input.json`, `medium_rules.json`, `medium_reference.json`, `medium_expected.json`
  - `hard_source_a.json`, `hard_source_b.json`, `hard_source_c.json`, `hard_spec.json`, `hard_expected.json`

3. Implement easy task class
- Target file: `hackathon/data_cleaning_env/server/tasks/easy.py`
- Implement metadata, deterministic data load, and exact-match grading for easy formula.

4. Implement medium task class
- Target file: `hackathon/data_cleaning_env/server/tasks/medium.py`
- Implement deterministic transformation grading with schema/field/constraint weighted scoring.

5. Implement hard task class
- Target file: `hackathon/data_cleaning_env/server/tasks/hard.py`
- Implement deterministic reconciliation grading with record matching/field correctness/conflict/completeness scoring.

6. Register tasks
- Target file: `hackathon/data_cleaning_env/server/tasks/__init__.py`
- Ensure `TASK_REGISTRY` keys are exactly `easy`, `medium`, `hard`.

7. Execute verification suite
- Run compile, registry, JSON parse, and overlap/count checks from Section 8.

## 6) Risks and Mitigations

| Risk | Impact | Mitigation | Verification Hook |
|---|---|---|---|
| File path resolution tied to CWD | Runtime file-not-found errors | Use module-relative `Path(__file__).resolve()` loading only | Registry import smoke test |
| Non-deterministic ordering during comparison | Score drift across runs | Normalize and sort records by deterministic keys | Repeat grade run yields identical output |
| Score escaping [0,1] due to arithmetic/tolerance bugs | Invalid grader behavior | Clamp outputs and test edge submissions | Assertion checks in verification script |
| Schema drift between input/rules/expected | False grading failures | Define required fields in this plan and validate JSON keys | JSON contract check script |
| Hard overlap too low/high vs target | Difficulty misalignment | Lock source counts and overlap target band (28-32) | Hard overlap inspection script |
| Registry mismatch (missing key or wrong max_steps) | Session verification fail | Assert exact key set and exact step limits | Registry assertion script |

## 7) Validation Checklist Mapped to Session 2 Spec

| Session 2 requirement | Tactical check | Pass condition |
|---|---|---|
| Plan first | Plan artifact exists before implementation | `hackathon/docs/sessions-plan/session-02-tactical-plan.md` exists |
| Data schema per task and required fields | Section 2 contracts defined for easy/medium/hard | Each task has explicit required field list |
| JSON naming and loading approach | Section 3 path and naming policy | All 11 required JSON files named exactly as specified |
| Determinism strategy | Section 4 deterministic rules | No randomness in task load/grade behavior |
| Hard task record counts and expected overlap | Section 2 hard contract | Source counts 50/45/40 and overlap in target band 28-32 |
| Implement easy/medium/hard tasks | Section 5 steps 3-5 | Three task classes load without error |
| Update TASK_REGISTRY | Section 5 step 6 | Registry keys exactly `easy`, `medium`, `hard` |
| Verification commands run | Section 8 command suite | All commands complete without assertion failure |
| Done criteria (no path/file ambiguity) | JSON load + import checks | No missing-file or malformed-JSON errors |

## 8) Exact Verification Commands and Pass Criteria

Run from repository root unless otherwise noted.

```bash
cd hackathon/data_cleaning_env

# Session-required compile check
python -m compileall .

# Session-required registry summary
python - <<'PY'
from server.tasks import TASK_REGISTRY
for k, t in TASK_REGISTRY.items():
    print(k, t.max_steps, len(t.input_data), t.total_gradable_fields)
PY

# Tactical strict registry assertions
python - <<'PY'
from server.tasks import TASK_REGISTRY
assert set(TASK_REGISTRY.keys()) == {"easy", "medium", "hard"}
assert TASK_REGISTRY["easy"].max_steps == 10
assert TASK_REGISTRY["medium"].max_steps == 15
assert TASK_REGISTRY["hard"].max_steps == 20
print("registry_contract_ok")
PY

# JSON presence and parse checks
python - <<'PY'
import json
from pathlib import Path

data_dir = Path("server/tasks/data")
required = [
    "easy_input.json", "easy_expected.json",
    "medium_input.json", "medium_rules.json", "medium_reference.json", "medium_expected.json",
    "hard_source_a.json", "hard_source_b.json", "hard_source_c.json", "hard_spec.json", "hard_expected.json",
]

for name in required:
    p = data_dir / name
    assert p.exists(), f"missing file: {name}"
    obj = json.loads(p.read_text(encoding="utf-8"))
    assert obj is not None, f"invalid json: {name}"

print("json_assets_ok")
PY

# Hard-task count and overlap sanity check (deterministic target band)
python - <<'PY'
import json
from pathlib import Path
from collections import Counter

def norm(v):
    return str(v or "").strip().lower()

def match_key(row):
    email = norm(row.get("email"))
    phone = norm(row.get("phone"))
    name = norm(row.get("name"))
    postal = norm(row.get("postal_code"))
    if email:
        return ("e", email)
    if phone:
        return ("p", phone)
    return ("n", f"{name}|{postal}")

d = Path("server/tasks/data")
a = json.loads((d / "hard_source_a.json").read_text(encoding="utf-8"))
b = json.loads((d / "hard_source_b.json").read_text(encoding="utf-8"))
c = json.loads((d / "hard_source_c.json").read_text(encoding="utf-8"))

assert len(a) == 50, f"hard_source_a count mismatch: {len(a)}"
assert len(b) == 45, f"hard_source_b count mismatch: {len(b)}"
assert len(c) == 40, f"hard_source_c count mismatch: {len(c)}"

presence = Counter()
for src in (a, b, c):
    seen = set()
    for row in src:
        k = match_key(row)
        if k in seen:
            continue
        seen.add(k)
        presence[k] += 1

overlap = sum(1 for v in presence.values() if v >= 2)
print("hard_overlap_entities", overlap)
assert 28 <= overlap <= 32, f"overlap out of band: {overlap}"
print("hard_overlap_ok")
PY
```

### Pass criteria
- `python -m compileall .` finishes without syntax errors.
- Registry summary runs without import/file errors.
- Registry assertions pass with exact keys and step limits (10, 15, 20).
- All 11 JSON assets exist and parse successfully.
- Hard source counts are exactly 50/45/40.
- Hard overlap sanity check is within 28-32 entities.
- No missing-file/path ambiguity is reported anywhere in command outputs.

## 9) Go / No-Go Decision

### Go conditions
- Plan artifact is complete (this file).
- Session 2 implementation is limited to scoped files in Section 1.
- Verification command suite in Section 8 is accepted as the execution gate.

### No-Go conditions
- Any request to change files outside Session 2 scope before completing scoped work.
- Any ambiguity about required JSON file names, task IDs, or max step limits.
- Any unresolved path-loading strategy that depends on runtime CWD.

### Current decision
- Go. Session 2 can proceed to implementation only after this tactical plan is accepted and followed.

## 10) Framework-Specific Consultation Notes

- No `ref-repos/OpenEnv` files were consulted for this Session 2 tactical planning step.
- If framework behavior ambiguity appears during implementation, consult only the minimal relevant `ref-repos/OpenEnv` files and record exact paths.