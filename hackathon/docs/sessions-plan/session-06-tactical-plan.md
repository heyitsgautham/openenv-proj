# Session 06 Tactical Plan: Docker Build, Runtime Checks, and Local Validation

Date: 2026-03-29
Session spec: Session 6 (Docker Build, Runtime Checks, and Local Validation)

Inputs read:
- hackathon/docs/sessions/06-session-docker-and-local-validation.md
- hackathon/docs/WINNING-PLAN.md
- hackathon/docs/PS.md

## 1) Scope and Non-Scope

### In Scope (Session 6 only)
- Create local dependency lock artifact:
  - hackathon/data_cleaning_env/uv.lock via uv lock
- Execute structural validator and address failures:
  - openenv validate --verbose
- Build and run the Docker image from:
  - hackathon/data_cleaning_env/server/Dockerfile
- Validate runtime endpoint contract on local container for:
  - /health
  - /metadata
  - /schema
  - /openapi.json
  - /mcp
- Run runtime validator against live URL:
  - openenv validate --url http://localhost:8000
- Iterate fixes only when needed to satisfy Session 6 validation gates.
- Produce evidence set for:
  - command outcomes
  - issues fixed during this session

### Out of Scope (deferred)
- New features or behavior changes not required to pass Session 6 checks.
- Inference baseline development/refactors (Session 5 scope).
- Hugging Face deployment and remote validation (Session 7 scope).
- README or submission packaging expansion not required for local validation.
- Large refactors unrelated to validator or container runtime failures.

## 2) Ordered Implementation Steps with Target Files

1. Confirm Session 6 planning precondition
- Target file:
  - hackathon/docs/sessions-plan/session-06-tactical-plan.md
- Gate:
  - plan file exists before any Session 6 execution/fix cycle.

2. Generate lock file
- Working directory:
  - hackathon/data_cleaning_env
- Command:
  - uv lock
- Primary artifact:
  - hackathon/data_cleaning_env/uv.lock
- If failure, likely targets:
  - hackathon/data_cleaning_env/pyproject.toml
  - environment tooling setup (uv/python resolution)

3. Run local structural validation
- Command:
  - openenv validate --verbose
- Expected checks include (from winning plan):
  - pyproject.toml present
  - uv.lock present
  - [project.scripts] has server entry ending in :main
  - openenv-core dependency present
  - server/app.py has main() and if __name__ block
- If failure, likely targets:
  - hackathon/data_cleaning_env/pyproject.toml
  - hackathon/data_cleaning_env/openenv.yaml
  - hackathon/data_cleaning_env/server/app.py
  - hackathon/data_cleaning_env/server/__init__.py (import path wiring only if needed)

4. Build Docker image
- Command:
  - docker build -t data-cleaning-env:latest -f server/Dockerfile .
- If failure, likely targets:
  - hackathon/data_cleaning_env/server/Dockerfile
  - hackathon/data_cleaning_env/pyproject.toml
  - hackathon/data_cleaning_env/uv.lock

5. Start container and keep it running for runtime checks
- Command:
  - docker run --rm -p 8000:8000 data-cleaning-env:latest
- If startup/import failure, likely targets:
  - hackathon/data_cleaning_env/server/app.py
  - hackathon/data_cleaning_env/server/data_cleaning_environment.py
  - hackathon/data_cleaning_env/models.py
  - hackathon/data_cleaning_env/pyproject.toml

6. Execute runtime endpoint matrix in second terminal
- Commands:
  - curl http://localhost:8000/health
  - curl http://localhost:8000/metadata
  - curl http://localhost:8000/schema
  - curl http://localhost:8000/openapi.json
  - curl -X POST http://localhost:8000/mcp -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","id":"session6","method":"tools/list","params":{}}'
- If failure, likely targets:
  - hackathon/data_cleaning_env/server/app.py
  - hackathon/data_cleaning_env/server/data_cleaning_environment.py
  - hackathon/data_cleaning_env/models.py
  - hackathon/data_cleaning_env/openenv.yaml

7. Run runtime validator against local URL
- Command:
  - openenv validate --url http://localhost:8000
- If failure, likely targets:
  - hackathon/data_cleaning_env/server/app.py
  - hackathon/data_cleaning_env/openenv.yaml
  - hackathon/data_cleaning_env/models.py

8. Close loop: if any validation fails, fix root cause and rerun full sequence
- Full rerun sequence:
  - uv lock
  - openenv validate --verbose
  - docker build ...
  - docker run ...
  - runtime endpoint matrix
  - openenv validate --url ...
- Evidence to collect:
  - final green outputs
  - concise list of issues fixed

## 3) Expected Failures, Risks, and Mitigations

| Risk / Expected Failure | Impact | Mitigation / Fix Strategy | Primary Target Files |
|---|---|---|---|
| uv lock fails (resolver/version mismatch) | Cannot produce mandatory uv.lock artifact | Align dependency constraints and python requirement; rerun uv lock | hackathon/data_cleaning_env/pyproject.toml |
| openenv validate --verbose fails script entry checks | Fails local structural gate | Ensure [project.scripts] includes server entry ending in :main and app.py contains main + if __name__ | hackathon/data_cleaning_env/pyproject.toml, hackathon/data_cleaning_env/server/app.py |
| openenv-core dependency check fails | Validator hard failure | Add/repair openenv-core dependency declaration and regenerate lock | hackathon/data_cleaning_env/pyproject.toml, hackathon/data_cleaning_env/uv.lock |
| Docker build fails (base image/dependency install) | Cannot reach runtime checks | Fix Dockerfile build steps, dependency install path, and lock usage | hackathon/data_cleaning_env/server/Dockerfile, hackathon/data_cleaning_env/pyproject.toml |
| Container starts then crashes (import/module path) | Endpoints unavailable | Resolve import fallbacks and PYTHONPATH/package wiring issues | hackathon/data_cleaning_env/server/app.py, hackathon/data_cleaning_env/pyproject.toml |
| /health or /openapi.json unavailable | Runtime contract fails | Ensure FastAPI app from create_app is exposed and server starts on port 8000 | hackathon/data_cleaning_env/server/app.py |
| /metadata missing required fields | Runtime validator fails | Ensure environment metadata contract returns required fields (name, description, version) | hackathon/data_cleaning_env/server/data_cleaning_environment.py |
| /schema shape mismatch | Action/observation/state schema validation fails | Align typed models and app wiring | hackathon/data_cleaning_env/models.py, hackathon/data_cleaning_env/server/app.py |
| /mcp call fails or non-JSON-RPC response | Runtime protocol check fails | Verify create_app wiring and endpoint availability; correct server routing issues | hackathon/data_cleaning_env/server/app.py |
| Port 8000 in use locally | False-negative runtime checks | Free port or run container on alternate host port and update URLs consistently | Execution environment (no source change unless required) |

## 4) Runtime Test Matrix (Session 6 Mandatory)

| Endpoint | Command | Expected Success Signal | Failure Triage Focus |
|---|---|---|---|
| /health | curl -fsS http://localhost:8000/health | JSON contains status=healthy | server/app.py, container startup logs |
| /metadata | curl -fsS http://localhost:8000/metadata | JSON includes name and description (version recommended) | data_cleaning_environment.py metadata method |
| /schema | curl -fsS http://localhost:8000/schema | JSON includes action_schema, observation_schema, state_schema | models.py and app wiring |
| /openapi.json | curl -fsS http://localhost:8000/openapi.json | JSON has info.version and expected endpoints | app.py create_app export and FastAPI boot |
| /mcp | curl -fsS -X POST http://localhost:8000/mcp -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","id":"session6","method":"tools/list","params":{}}' | JSON-RPC object with jsonrpc=2.0 and matching id | create_app route exposure in app.py |

## 5) Validation Checklist Mapped to Session 6 Spec

| Session 6 requirement | Tactical check | Pass condition |
|---|---|---|
| Plan first | This tactical plan is created before execution | File exists at hackathon/docs/sessions-plan/session-06-tactical-plan.md |
| Plan includes command order | Section 2 ordered steps | Steps run in exact sequence from lock to runtime validate |
| Plan includes expected failures and fix strategy | Section 3 | Each likely failure has mitigation and target files |
| Plan includes runtime test matrix (health/metadata/schema/openapi/mcp) | Section 4 | All five endpoints tested with explicit expected signal |
| Run iterative fix cycle | Section 2 step 8 | Any failure triggers root-cause fix + full rerun |
| Docker image builds cleanly | Section 6 command set | docker build exits 0 and image tag exists |
| Container serves required endpoints | Section 4 matrix | All endpoint checks return successful JSON responses |
| openenv validate passes locally (structure) | Section 6 command set | openenv validate --verbose exits 0 |
| openenv validate passes against runtime URL | Section 6 command set | openenv validate --url http://localhost:8000 exits 0 |
| Deliver uv.lock in working tree | Section 2 step 2 | uv.lock present and tracked for commit |
| Report evidence and issues fixed | Session 6 completion report | Command outcomes + issue list recorded |

## 6) Exact Verification Commands and Pass Criteria

Run from repository root unless noted.

### 6.1 Structural and build sequence (Terminal A)

cd hackathon/data_cleaning_env
uv lock
openenv validate --verbose
docker build -t data-cleaning-env:latest -f server/Dockerfile .

Pass criteria:
- uv lock exits 0 and uv.lock exists at hackathon/data_cleaning_env/uv.lock.
- openenv validate --verbose exits 0 with no failing checks.
- docker build exits 0 and produces image data-cleaning-env:latest.

### 6.2 Runtime server (Terminal A, keep running)

cd hackathon/data_cleaning_env
docker run --rm -p 8000:8000 data-cleaning-env:latest

Pass criteria:
- Container process stays alive.
- No startup traceback.
- Service listens on 0.0.0.0:8000.

### 6.3 Runtime endpoint matrix (Terminal B)

curl -fsS http://localhost:8000/health
curl -fsS http://localhost:8000/metadata
curl -fsS http://localhost:8000/schema
curl -fsS http://localhost:8000/openapi.json
curl -fsS -X POST http://localhost:8000/mcp -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","id":"session6","method":"tools/list","params":{}}'
openenv validate --url http://localhost:8000

Pass criteria:
- Each curl command exits 0 and returns valid JSON payload for the target endpoint.
- /health reports healthy status.
- /metadata includes name and description.
- /schema includes action/observation/state schema payloads.
- /openapi.json includes info.version.
- /mcp returns JSON-RPC shaped response (jsonrpc=2.0 and id=session6).
- openenv validate --url exits 0 with all runtime checks passing.

### 6.4 Failure handling rule (mandatory)

If any command in 6.1-6.3 fails:
- Fix root cause in the mapped target file(s).
- Rerun full sequence from 6.1 onward (not partial reruns only).

Pass criteria:
- Final run has all checks green in one continuous pass.

## 7) Go or No-Go Decision

### Go Conditions
- Tactical plan artifact exists and is complete.
- Structural validation passes (openenv validate --verbose).
- Docker image builds and container serves runtime endpoints.
- Runtime endpoint matrix passes for health, metadata, schema, openapi, and mcp.
- openenv validate --url http://localhost:8000 passes.
- uv.lock exists and is ready to be committed.
- Evidence and issue-fix list are documented.

### No-Go Conditions
- Any required validator check remains failing.
- Container cannot stay healthy and serve required endpoints.
- Runtime matrix missing any required endpoint or contract response.
- Fixes are not revalidated by full sequence rerun.

### Current Decision
- Go to Session 6 execution phase after this tactical plan artifact is approved.

## 8) Framework-Specific Consultation Notes

- No files under ref-repos/OpenEnv were consulted for this Session 6 planning artifact.
- If framework behavior ambiguity appears during execution/fixes, consult only minimal relevant files in ref-repos/OpenEnv and record exact consulted paths in the implementation report.
