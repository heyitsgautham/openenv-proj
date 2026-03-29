# Session 6: Docker Build, Runtime Checks, and Local Validation

Estimated effort: 2-3 hours

## Goal
Prove the environment passes local structural and runtime validation before deployment.

## Inputs
- Sessions 1-5 outputs
- hackathon/docs/WINNING-PLAN.md (validation commands)

## Tactical Plan Output (Plan Prompt Artifact)
- hackathon/docs/sessions-plan/session-06-tactical-plan.md

## Mandatory Workflow
1. Plan first.
2. Save the tactical plan to the Tactical Plan Output file.
3. Implement/execute using both this session spec and the tactical plan.
4. Verify against checks from both this session spec and the tactical plan.
5. Report artifacts and blockers.

## Step 1: Plan First
Plan should include:
- Order of local validation commands.
- Expected failures and fix strategy.
- Runtime test matrix for health, metadata, schema, openapi, mcp.

Do not execute until plan is explicit.
The plan must be saved to the Tactical Plan Output file.

## Step 2: Implement and Execute
Run and fix issues iteratively:

Precondition: Tactical Plan Output file exists.

```bash
cd hackathon/data_cleaning_env
uv lock
openenv validate --verbose
docker build -t data-cleaning-env:latest -f server/Dockerfile .
docker run -p 8000:8000 data-cleaning-env:latest
```

In a second terminal:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/metadata
curl http://localhost:8000/schema
curl http://localhost:8000/openapi.json
openenv validate --url http://localhost:8000
```

## Step 3: Verify
Verification must confirm:
- Docker image builds cleanly.
- Container serves all required endpoints.
- openenv validate passes for both local structure and runtime URL.
- All checks defined in the tactical plan are completed.

If validation fails, fix root cause and re-run full command sequence.

## Deliverables
- uv.lock committed in working tree.
- Runtime validation evidence with command outcomes.
- List of issues fixed during this session.

## Done Criteria
- Local system is green on validator checks.
- Environment is deployment-ready.
