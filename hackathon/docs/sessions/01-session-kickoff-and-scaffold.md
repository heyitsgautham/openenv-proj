# Session 1: Kickoff, Scope Lock, and Scaffold

Estimated effort: 2-3 hours

## Goal
Create a clean, canonical OpenEnv project scaffold for the Data Cleaning environment with correct package structure and entrypoints.

## Inputs
- hackathon/docs/WINNING-PLAN.md
- hackathon/docs/PS.md

## Tactical Plan Output (Plan Prompt Artifact)
- hackathon/docs/sessions-plan/session-01-tactical-plan.md

## Mandatory Workflow
1. Plan first.
2. Save the tactical plan to the Tactical Plan Output file.
3. Implement/execute using both this session spec and the tactical plan.
4. Verify against checks from both this session spec and the tactical plan.
5. Report artifacts and blockers.

## Step 1: Plan First
Before editing files, produce a short plan with:
- Exact file tree to create under hackathon/data_cleaning_env.
- Dependency decisions for pyproject.toml.
- Order of implementation so imports resolve.
- Risks and mitigations (entrypoint mismatch, package path mismatch, missing server script).

Do not start coding until this plan is written.
The plan must be saved to the Tactical Plan Output file.

## Step 2: Implement and Execute
Create this structure and minimum viable contents:

Precondition: Tactical Plan Output file exists.

- hackathon/data_cleaning_env/__init__.py
- hackathon/data_cleaning_env/models.py
- hackathon/data_cleaning_env/client.py
- hackathon/data_cleaning_env/openenv.yaml
- hackathon/data_cleaning_env/pyproject.toml
- hackathon/data_cleaning_env/server/__init__.py
- hackathon/data_cleaning_env/server/app.py
- hackathon/data_cleaning_env/server/Dockerfile
- hackathon/data_cleaning_env/server/tasks/__init__.py
- hackathon/data_cleaning_env/server/tasks/base.py
- hackathon/data_cleaning_env/server/tasks/data/ (empty for now)

Implementation notes:
- Follow the exact create_app pattern from WINNING-PLAN.
- Ensure server script points to data_cleaning_env.server.app:main.
- Keep models and client as compile-safe skeletons if logic is unfinished.

## Step 3: Verify
Run:

```bash
cd hackathon/data_cleaning_env
python -m compileall .
rg -n "def main\(|if __name__ == \"__main__\"|create_app\(" server/app.py
rg -n "\[project\.scripts\]|server\s*=\s*\"data_cleaning_env\.server\.app:main\"" pyproject.toml
```

Verification must confirm:
- No syntax errors.
- Entry point is present and correct.
- Package layout matches planned tree.
- All checks defined in the tactical plan are completed.

## Deliverables
- All scaffold files created.
- Verification output summary.
- Short handoff note listing what Session 2 depends on.

## Done Criteria
- Scaffold compiles.
- Imports resolve for created files.
- No unresolved package path ambiguity.
