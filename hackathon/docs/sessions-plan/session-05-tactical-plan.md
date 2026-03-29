# Session 05 Tactical Plan: Inference Baseline and Robust Connection Logic

Date: 2026-03-29
Session spec: Session 5 (Inference Baseline and Robust Connection Logic)

Inputs read:
- hackathon/docs/sessions/05-session-inference-baseline.md
- hackathon/docs/WINNING-PLAN.md
- hackathon/docs/PS.md

## 1) Scope and Non-Scope

### In Scope (Session 5 only)
- Plan and then implement the baseline inference script in:
  - hackathon/data_cleaning_env/inference.py
- Use OpenAI Python client only for model calls.
- Enforce credential handling with exact API key fallback order:
  - HF_TOKEN, then API_KEY, then OPENAI_API_KEY.
- Enforce connection fallback order:
  - ENV_URL first, then Docker fallback via asyncio.run(from_docker_image()).
- Run all three tasks (easy, medium, hard) and print:
  - per-task score
  - average score
- Define prompt format and response parsing strategy for robust JSON handling.
- Define per-task loop limits and early-stop behavior for evaluator-safe runtime.
- Define verification commands and pass/fail criteria for Session 5 readiness.

### Out of Scope (deferred)
- Any edits to environment runtime/server logic:
  - hackathon/data_cleaning_env/server/data_cleaning_environment.py
  - hackathon/data_cleaning_env/server/graders.py
  - hackathon/data_cleaning_env/server/tasks/*
- Dockerfile changes, deployment pipeline, and Hugging Face publish work.
- README expansion and submission packaging.
- Refactors not required to satisfy Session 5 inference requirements.

## 2) Ordered Implementation Steps with Target Files

1. Confirm precondition artifact exists
- Target: hackathon/docs/sessions-plan/session-05-tactical-plan.md
- Gate: this plan file is saved before any Session 5 code edits.

2. Create baseline script skeleton and configuration constants
- Target: hackathon/data_cleaning_env/inference.py
- Add constants for:
  - API_BASE_URL (default fallback)
  - MODEL_NAME
  - ENV_URL
  - DOCKER_IMAGE
  - TASKS = [easy, medium, hard]
  - TASK_MAX_STEPS = {easy: 10, medium: 15, hard: 20}
  - generation settings (temperature, max_tokens)

3. Implement credential validation and fail-fast messages
- Target: hackathon/data_cleaning_env/inference.py
- Behavior:
  - Resolve API key in exact order: HF_TOKEN, API_KEY, OPENAI_API_KEY.
  - Exit early with clear error when API key missing.
  - Exit early with clear error when MODEL_NAME missing.
  - No hardcoded secrets or model credentials.

4. Implement prompt format and parsing strategy
- Target: hackathon/data_cleaning_env/inference.py
- Prompt design:
  - System prompt: return JSON array only.
  - User prompt includes task description, target schema, full input data, and prior validation errors.
- Parsing strategy:
  - Strip whitespace.
  - Remove optional markdown fences.
  - Attempt json.loads.
  - Accept only list payload for action data.
  - On parse failure, produce a safe fallback path (skip step or submit empty list according to final implementation choice), with explicit log line.

5. Implement dual-mode environment connection function
- Target: hackathon/data_cleaning_env/inference.py
- Connection order:
  - Probe ENV_URL health first.
  - If reachable: connect via DataCleanEnv(base_url=ENV_URL).sync().
  - If unreachable: fallback to Docker using asyncio.run(DataCleanEnv.from_docker_image(DOCKER_IMAGE)), then sync.
- Ensure logs indicate which branch was selected.

6. Implement task execution loop with strict limits
- Target: hackathon/data_cleaning_env/inference.py
- Loop behavior:
  - Run tasks in order: easy, medium, hard.
  - Per task, enforce max steps from TASK_MAX_STEPS.
  - Stop early when result.done is true.
  - Stop early when score reaches near-perfect threshold (>= 0.99).
  - Track and report best score per task.

7. Implement summary output and cleanup
- Target: hackathon/data_cleaning_env/inference.py
- Output requirements:
  - clear per-task score lines
  - final average score line
- Ensure environment close in finally block.

8. Execute verification suite and capture evidence
- Targets:
  - session-required commands
  - tactical supplemental checks for fail-fast and branch selection logs

## 3) Risks and Mitigations

| Risk | Impact | Mitigation | Verification Hook |
|---|---|---|---|
| Incorrect credential precedence | Evaluator may reject or fail unexpectedly | Hard-code fallback logic order in one place: HF_TOKEN -> API_KEY -> OPENAI_API_KEY | rg pattern check plus env-matrix runtime checks |
| Missing fail-fast behavior | Opaque failures and non-reproducible runs | Validate key and model before env connection and before API calls | run without credentials and without MODEL_NAME |
| Connection ambiguity (URL vs Docker) | Script fails in one evaluator mode | URL-first probe with explicit Docker fallback | branch log checks for both reachable and unreachable ENV_URL scenarios |
| Async misuse for from_docker_image | Runtime exception on fallback path | Use asyncio.run around from_docker_image call in sync script | rg pattern check for asyncio.run and fallback execution path |
| Prompt too weak or parser brittle | Low baseline score or repeated parse failures | JSON-only system instruction, robust fence stripping, strict list validation | run task loop and inspect parse-failure logs |
| Missing task coverage | Fails mandatory all-task baseline requirement | Fixed TASKS list includes easy, medium, hard in order | output contains exactly three task result lines |
| Missing summary metrics | Baseline result not evaluator-friendly | print per-task and average score | output includes average score line |
| Runtime exceeds practical limits | Infra timeout risk | enforce per-task max steps and early-stop on done/near-perfect | logs show capped loop counts and early-stop behavior |
| Hardcoded secrets | Security and policy violation | read credentials only from environment variables | source grep for credential literals and runtime env-only behavior |

## 4) Validation Checklist Mapped to Session 5 Spec

| Session 5 requirement | Tactical check | Pass condition |
|---|---|---|
| Plan first | This plan exists before code edits | file saved at required tactical-plan path |
| Include prompt format and parsing strategy | Section 2 steps 4 and 6 | strategy explicitly documented and implemented |
| Include credential fallback order | Section 2 step 3 | exact order HF_TOKEN -> API_KEY -> OPENAI_API_KEY |
| Include connection fallback order | Section 2 step 5 | ENV_URL probe first, Docker fallback second |
| Include loop limits and early-stop rules | Section 2 step 6 | TASK_MAX_STEPS enforced, done and >=0.99 early stop |
| Use OpenAI Python client only | source scan for import and usage | from openai import OpenAI present; no alternate LLM clients |
| Runs all three tasks | runtime output review | easy, medium, hard all executed and reported |
| Prints per-task and average scores | runtime output review | per-task lines plus final average line |
| If credentials unavailable, fail fast clearly | negative runtime check | intentional, readable error message and non-zero exit |
| No hardcoded secrets | source review | no embedded API keys/tokens in script |
| Control flow supports both evaluator connection scenarios | runtime branch tests | URL-first path and Docker fallback path both observable/valid |

## 5) Exact Verification Commands and Pass Criteria

Run from repository root unless stated otherwise.

### 5.1 Session-required structural checks

cd hackathon/data_cleaning_env
python -m compileall inference.py
rg -n "from openai import OpenAI|HF_TOKEN|API_KEY|OPENAI_API_KEY|ENV_URL|DOCKER_IMAGE|asyncio.run\(" inference.py

Pass criteria:
- compileall exits successfully with no syntax errors.
- rg returns matches proving required import, env vars, and asyncio Docker fallback usage are present.

### 5.2 Session-required execution check

cd hackathon/data_cleaning_env
python inference.py

Pass criteria:
- With valid credentials and reachable environment path, script runs tasks and prints per-task plus average scores.
- If credentials are missing, script exits early with clear intentional message (not an unhandled traceback).

### 5.3 Tactical supplement: fail-fast credential behavior

cd hackathon/data_cleaning_env
env -u HF_TOKEN -u API_KEY -u OPENAI_API_KEY python inference.py

Pass criteria:
- Non-zero exit.
- Error text clearly states missing API key variables and accepted fallback names.

cd hackathon/data_cleaning_env
env HF_TOKEN=dummy-token MODEL_NAME= API_BASE_URL=https://router.huggingface.co/v1 python inference.py

Pass criteria:
- Non-zero exit.
- Error text clearly states MODEL_NAME is required.

### 5.4 Tactical supplement: connection branch behavior

Unreachable URL forcing Docker fallback branch:

cd hackathon/data_cleaning_env
env HF_TOKEN=dummy-token MODEL_NAME=dummy-model API_BASE_URL=https://router.huggingface.co/v1 ENV_URL=http://127.0.0.1:65535 DOCKER_IMAGE=data-cleaning-env:latest python inference.py

Pass criteria:
- Output indicates ENV_URL was not reachable.
- Output indicates Docker fallback path was attempted.
- If Docker image is unavailable, failure message is explicit and intentional.

Reachable URL path (when server is running separately):

cd hackathon/data_cleaning_env
env HF_TOKEN=dummy-token MODEL_NAME=dummy-model API_BASE_URL=https://router.huggingface.co/v1 ENV_URL=http://127.0.0.1:8000 python inference.py

Pass criteria:
- Output indicates connection to running server at ENV_URL.
- Docker fallback is not used in this run.

### 5.5 Tactical supplement: no hardcoded secret scan

cd hackathon/data_cleaning_env
rg -n "hf_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}|OPENAI_API_KEY\s*=\s*['\"][^'\"]+['\"]" inference.py

Pass criteria:
- No matches for hardcoded credential values.

## 6) Go or No-Go Decision

### Go Conditions
- Plan file exists at required path and is complete.
- Implementation remains limited to Session 5 target file(s).
- All Session-required checks in Section 5.1 and 5.2 pass.
- Tactical supplemental checks in Sections 5.3 to 5.5 pass or produce documented intentional fail-fast outcomes where external dependencies are missing.

### No-Go Conditions
- Credential fallback order differs from required order.
- Connection fallback order does not prioritize ENV_URL first.
- asyncio.run Docker fallback path missing.
- Any hardcoded secret detected.
- Script does not run all three tasks or omits average score output.
- Fail-fast behavior is unclear or relies on uncaught exceptions.

### Current Decision
- Go for Session 5 implementation after this tactical plan artifact is approved.

## 7) Framework-Specific Consultation Notes

- No files under ref-repos/OpenEnv were consulted for this plan-only Session 5 step.
- If framework ambiguity appears during implementation, consult only minimal relevant OpenEnv files and record exact consulted paths in the implementation report.
