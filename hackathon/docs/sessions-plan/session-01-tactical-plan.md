# Session 01 Tactical Plan: Kickoff, Scope Lock, and Scaffold

Date: 2026-03-29
Session spec: Session 1 (Kickoff, Scope Lock, and Scaffold)

## 1) Scope and Non-Scope

### In Scope (Session 1 only)
- Create the canonical scaffold under `hackathon/data_cleaning_env`.
- Create compile-safe skeleton content for:
  - package root files
  - server entrypoint files
  - task package placeholders
- Lock entrypoint wiring to `data_cleaning_env.server.app:main`.
- Define minimal dependency and packaging decisions in `pyproject.toml` so imports and script resolution are unambiguous.
- Run Session 1 verification commands and capture pass/fail outcomes.

### Out of Scope (deferred to later sessions)
- Implement full environment logic (`reset`, `step`, `state`) beyond skeleton compatibility.
- Implement graders or task logic for easy/medium/hard.
- Create task JSON data contents.
- Build inference workflow or benchmark scoring.
- End-to-end Docker runtime validation, HF deployment, and submission packaging.
- Full README and docs completion.

## 2) Exact File Tree to Create (Session 1)

```text
hackathon/data_cleaning_env/
├── __init__.py
├── models.py
├── client.py
├── openenv.yaml
├── pyproject.toml
└── server/
    ├── __init__.py
    ├── app.py
    ├── Dockerfile
    └── tasks/
        ├── __init__.py
        ├── base.py
        └── data/
```

Note: `server/tasks/data/` is intentionally empty in this session.

## 3) Dependency and Packaging Decisions for pyproject.toml

### Required decisions
- Build backend:
  - `setuptools.build_meta`
- Python version:
  - `>=3.11`
- Runtime dependency:
  - `openenv-core[core]>=0.2.2`
- Script entrypoint:
  - `[project.scripts]`
  - `server = "data_cleaning_env.server.app:main"`
- Package discovery (explicit to avoid path ambiguity in this repo layout):
  - `data_cleaning_env`
  - `data_cleaning_env.server`
  - `data_cleaning_env.server.tasks`
- Package-dir mapping:
  - `data_cleaning_env = "."`

### Optional (safe for Session 1)
- Dev extras for future sessions: `pytest`, `pytest-cov`

## 4) Ordered Implementation Steps with Target Files

Order is designed to avoid transient import and package-resolution failures.

1. Create directories
   - `hackathon/data_cleaning_env/`
   - `hackathon/data_cleaning_env/server/`
   - `hackathon/data_cleaning_env/server/tasks/`
   - `hackathon/data_cleaning_env/server/tasks/data/`

2. Create package anchors first
   - `hackathon/data_cleaning_env/__init__.py`
   - `hackathon/data_cleaning_env/server/__init__.py`
   - `hackathon/data_cleaning_env/server/tasks/__init__.py`

3. Create typed skeletons
   - `hackathon/data_cleaning_env/models.py`
   - `hackathon/data_cleaning_env/client.py`

4. Create server entrypoint with canonical pattern
   - `hackathon/data_cleaning_env/server/app.py`
   - Must include:
     - `create_app(...)`
     - `def main(...)`
     - `if __name__ == "__main__"`

5. Create runtime and packaging config
   - `hackathon/data_cleaning_env/openenv.yaml`
   - `hackathon/data_cleaning_env/pyproject.toml`

6. Create container scaffold file
   - `hackathon/data_cleaning_env/server/Dockerfile`

7. Create task base placeholder
   - `hackathon/data_cleaning_env/server/tasks/base.py`

8. Run verification suite (Section 7 of this plan)

## 5) Risks and Mitigations

| Risk | Why it matters in Session 1 | Mitigation | Verification hook |
|---|---|---|---|
| Entrypoint mismatch (`server` script wrong target) | Validator local checks fail early | Hardcode `server = "data_cleaning_env.server.app:main"` | `rg` check on `pyproject.toml` |
| Package path mismatch (`package-dir`/imports) | Import ambiguity in monorepo layout | Use explicit package list + package-dir mapping; keep imports package-relative | compile + import smoke check |
| Missing `main()` in server app | Fails required validator checks | Include `def main(` explicitly | `rg` check on `server/app.py` |
| Missing `if __name__ == "__main__"` block | Fails required validator checks | Add block in `server/app.py` | `rg` check on `server/app.py` |
| Incorrect `create_app` wiring pattern | Runtime wiring drift from OpenEnv expectations | Use canonical pattern from WINNING-PLAN | `rg` check for `create_app(` |
| Untracked empty `tasks/data/` directory | Can disappear in git workflows | Create directory as explicit scaffold artifact for this session | tree/listing check |
| Premature scope creep into Session 2+ | Wastes time and raises integration risk | Enforce strict non-scope list above | session checklist sign-off |

## 6) Validation Checklist Mapped to Session 1 Spec

| Session 1 requirement | Tactical check | Pass condition |
|---|---|---|
| Plan first before coding | This tactical plan file exists | `hackathon/docs/sessions-plan/session-01-tactical-plan.md` exists |
| Exact scaffold tree created | Compare workspace tree to Section 2 | All listed files/dirs exist; no required file missing |
| Dependency decisions locked | Review `pyproject.toml` keys from Section 3 | `openenv-core` dependency, script target, package mapping all present |
| Correct server entrypoint pattern | Inspect `server/app.py` | Contains `create_app(`, `def main(`, and `if __name__ == "__main__"` |
| No syntax errors | Run compile check | `python -m compileall .` reports no errors |
| Entry point present and correct | Run grep checks | Regex checks match expected lines |
| Package layout matches planned tree | Run tree/list command | Output matches Section 2 |
| Imports resolve for created files | Run import smoke check | Import command exits 0 |
| No unresolved package path ambiguity | Validate package/script wiring consistency | script target and package mapping are internally consistent |

## 7) Exact Verification Commands and Pass Criteria

Run from repository root unless noted.

```bash
# Session-mandated checks
cd hackathon/data_cleaning_env
python -m compileall .
rg -n "def main\(|if __name__ == \"__main__\"|create_app\(" server/app.py
rg -n "\[project\.scripts\]|server\s*=\s*\"data_cleaning_env\.server\.app:main\"" pyproject.toml

# Tactical plan additional checks
find . -maxdepth 4 -print | sort
cd ..
python -c "import data_cleaning_env; from data_cleaning_env import DataCleanAction, DataCleanObservation, DataCleanState, DataCleanEnv; print('imports_ok')"
```

### Pass criteria
- `python -m compileall .` completes with no syntax errors.
- `rg` on `server/app.py` returns matches for all three required patterns.
- `rg` on `pyproject.toml` returns matches for `[project.scripts]` and exact `server` target.
- `find` output confirms all required Session 1 scaffold paths exist.
- Python import smoke check prints `imports_ok` and exits with status 0.

## 8) Go / No-Go Decision Gate

### Go
- Proceed to Session 1 Step 2 implementation only if all checklist items in Section 6 are satisfiable and no blocker remains on package naming, script target, or entrypoint pattern.

### No-Go
- Stop and resolve before coding if any of the following is true:
  - Script target cannot be set to `data_cleaning_env.server.app:main`.
  - `server/app.py` cannot include `main` and `__main__` block.
  - Package mapping in `pyproject.toml` remains ambiguous.
  - Required scaffold tree cannot be created as specified.

### Current decision for this session state
- Go: plan artifact is defined, scoped, and ready to drive Session 1 implementation.

## 9) Framework-Specific Consultation Notes

- No direct `ref-repos/OpenEnv` file inspection was needed for this plan-only step.
- If framework ambiguity appears during implementation, consult only the minimal OpenEnv source files relevant to that ambiguity and record exact paths.