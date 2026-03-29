# OpenEnv Hackathon Approach (Research-Based Plan)

This document captures the complete approach discussed for the hackathon problem statement in `hackathon/docs/PS.md`, grounded in this repo's course content and the `ref-repos/OpenEnv` implementation/docs.

## 1) Objective

Build a complete OpenEnv environment for a real-world task (not a toy/game) with:

- Full OpenEnv spec compliance
- At least 3 tasks with deterministic graders (easy -> medium -> hard)
- Reward shaping with partial progress signals
- Reproducible baseline inference in root `inference.py`
- Dockerized deployment to Hugging Face Spaces
- Clear README with setup, spaces, tasks, and baseline scores

Primary source: `hackathon/docs/PS.md`

## 2) Core Recommendation

Recommended domain: **Email Triage and Prioritization**

Why this is the strongest option:

- High real-world utility and obvious practical relevance
- Easy to make deterministic grading in [0.0, 1.0]
- Easy to shape intermediate rewards
- Lightweight runtime (fits 2 vCPU / 8GB constraints)
- Lower infra risk than domains that require external app servers

Backup options:

1. Code review assistant
2. Customer support triage
3. Data cleaning and validation

## 3) Research Sources Used

- Hackathon requirements:
  - `hackathon/docs/PS.md`
- Course flow:
  - `README.md`
  - `module-1/README.md`
  - `module-2/README.md`
  - `module-3/README.md`
  - `module-4/README.md`
  - `module-5/README.md`
- OpenEnv build/deploy docs:
  - `ref-repos/OpenEnv/docs/environment-builder.md`
  - `ref-repos/OpenEnv/docs/contributing-envs.md`
  - `ref-repos/OpenEnv/docs/quickstart.md`
  - `ref-repos/OpenEnv/docs/cli.md`
- OpenEnv validator and runtime contract internals:
  - `ref-repos/OpenEnv/src/openenv/cli/_validation.py`
  - `ref-repos/OpenEnv/src/openenv/cli/_cli_utils.py`
  - `ref-repos/OpenEnv/src/openenv/cli/commands/validate.py`
  - `ref-repos/OpenEnv/src/openenv/core/env_server/interfaces.py`
  - `ref-repos/OpenEnv/src/openenv/core/env_server/types.py`
  - `ref-repos/OpenEnv/src/openenv/core/env_server/http_server.py`
- Grading and rubric patterns:
  - `ref-repos/OpenEnv/rfcs/004-rubrics.md`
  - `ref-repos/OpenEnv/src/openenv/core/rubrics/base.py`
  - `ref-repos/OpenEnv/src/openenv/core/rubrics/trajectory.py`
  - `ref-repos/OpenEnv/envs/repl_env/rubrics.py`
  - `ref-repos/OpenEnv/envs/finqa_env/server/rewards.py`
- Inference templates (OpenAI client + env vars):
  - `ref-repos/OpenEnv/examples/finqa_inference.py`
  - `ref-repos/OpenEnv/examples/coding_env_inference.py`
  - `ref-repos/OpenEnv/examples/textarena_wordle_inference.py`

## 4) Compliance Checklist (Pass/Fail)

All items below should be treated as gates.

### Functional

- Real-world task simulation (not game/toy)
- Typed Action / Observation / State models
- Correct `reset()`, `step()`, and `state` behavior
- `openenv.yaml` present and valid
- >= 3 tasks with deterministic graders (easy/medium/hard)
- Grader outputs in [0.0, 1.0]
- Reward shaping over full trajectory (not terminal-only)
- Root `inference.py` using OpenAI client + required env vars

### Non-functional

- Dockerfile builds and starts cleanly
- Hugging Face Space deploys and responds
- README contains environment motivation, spaces, tasks, setup, baseline scores

### Disqualification risks

- No deployment response
- Constant-score graders
- Missing baseline inference script
- Fewer than 3 tasks
- Plagiarized or trivial copy

## 5) Phase Plan

## Phase 0 - Domain Lock and Task Spec (0.5 day)

Outputs:

- Domain selected (recommend: email triage)
- Three task specs with explicit grading formula and expected behavior
- Episode boundaries and max step limits finalized

Validation gate:

- Review each task for deterministic grading and non-binary reward path

## Phase 1 - Scaffold and Spec Skeleton (0.5 to 1 day)

Outputs:

- Scaffold environment via `openenv init <env_name>`
- Models, client, server app, Dockerfile, and manifest created
- Basic package and entrypoint wiring verified

Commands:

```bash
openenv init email_triage_env
cd email_triage_env
openenv validate --verbose
```

Validation gate:

- Local structure passes validation

## Phase 2 - Environment Core Implementation (1 to 1.5 days)

Outputs:

- Typed models finalized
- Environment logic for `reset`, `step`, and `state` implemented
- Task registry and task-specific initialization implemented
- Clean state reset semantics verified

Validation gate:

- Manual deterministic replay checks across multiple resets and seeds

## Phase 3 - Graders and Reward Shaping (1 to 1.5 days)

Outputs:

- 3 deterministic graders in [0.0, 1.0]
- Partial progress reward and penalties implemented
- Task difficulty progression (easy -> medium -> hard)

Validation gate:

- Reward distribution is non-constant
- Easy task scores higher than hard under same baseline agent

## Phase 4 - Baseline Inference Script (1 day)

Outputs:

- Root `inference.py`
- Uses OpenAI client and env vars:
  - `API_BASE_URL`
  - `MODEL_NAME`
  - `HF_TOKEN`
- Runs all three tasks and emits reproducible score summary

Validation gate:

- Script completes without error
- Runtime under 20 minutes on target constraints

## Phase 5 - Docker and Runtime Validation (0.5 to 1 day)

Outputs:

- Docker image builds and runs locally
- Local runtime endpoint validation passes

Commands:

```bash
docker build -t email-triage-env:latest -f server/Dockerfile .
docker run -p 8000:8000 email-triage-env:latest
openenv validate --url http://localhost:8000
```

Validation gate:

- Runtime criteria pass (OpenAPI, health, metadata, schema, endpoint consistency)

## Phase 6 - Docs and HF Deployment (1 day)

Outputs:

- README finalized with all required sections
- HF Space deployed with `openenv` tag and working API
- Baseline scores recorded in README

Commands:

```bash
hf auth login
openenv push --repo-id <username>/<space-name>
openenv validate https://<username>-<space-name>.hf.space
```

Validation gate:

- Space responds with healthy runtime and reset capability

## 6) VS Code vs External Dependencies

### What can be done fully in VS Code

- Design and coding of environment, tasks, graders, and rewards
- Local validation and tests
- Docker build and local container run
- Inference script implementation and dry runs

### What needs external systems

- Hugging Face account + token for deployment (`openenv push`)
- OpenAI-compatible endpoint credentials for inference
- Internet connectivity for model calls and space deployment

## 7) Tooling: Required vs Optional

### Required

- Python 3.11+
- `openenv-core` (CLI + runtime)
- `uv` (dependency locking/workflow)
- Docker
- `openai` Python SDK

### Required environment variables for baseline

```bash
export API_BASE_URL="https://router.huggingface.co/v1"
export MODEL_NAME="openai/gpt-oss-120b:novita"
export HF_TOKEN="hf_xxx"
```

### Optional

- pytest and coverage tooling
- lint/format tools (ruff, black)
- custom UI enhancements

## 8) Do We Need MCP?

Short answer: **not required for this hackathon submission path**.

You can build a complete submission with standard OpenEnv API patterns and deterministic graders. MCP can be used if your domain truly benefits from tool-calling workflows, but it adds complexity and is not necessary to pass baseline requirements.

## 9) Validator-Driven Hard Requirements (Important)

From OpenEnv validator internals:

- Local validation checks include:
  - `pyproject.toml`
  - `uv.lock`
  - project script entrypoint for server
  - `server/app.py` with callable `main()` flow
- Runtime validation checks include:
  - `/openapi.json` with version
  - `/health`
  - `/metadata`
  - `/schema`
  - `/mcp`
  - endpoint-mode consistency

Reference files:

- `ref-repos/OpenEnv/src/openenv/cli/_validation.py`
- `ref-repos/OpenEnv/src/openenv/cli/commands/validate.py`

## 10) Common Failure Modes and Mitigations

1. Constant grader outputs

- Risk: disqualification
- Mitigation: test score spread over varied trajectories

2. Sparse reward only at terminal state

- Risk: weak evaluation and poor learning signal
- Mitigation: add milestone-based partial rewards and negative penalties for bad actions

3. Bad reset semantics (state leakage)

- Risk: non-reproducible scores
- Mitigation: fully reinitialize state on `reset()`

4. Baseline script hardcodes model settings

- Risk: fails evaluator infra expectations
- Mitigation: read from required env vars only

5. Docker builds but runtime endpoints fail

- Risk: phase-1 automation fail
- Mitigation: run `openenv validate --url` on local container before push

## 11) Suggested Task Blueprint (Email Triage)

Easy task:

- Binary spam/ham classification
- Grader: exact-label match with deterministic rulebook
- Reward: +1 correct, 0 incorrect, small step penalty for irrelevant actions

Medium task:

- Priority ranking of inbox emails
- Grader: normalized ranking score to [0,1]
- Reward: partial credit for near-correct ordering

Hard task:

- Multi-label decision (urgent/action-required/fyi/escalate)
- Grader: weighted micro-F1 style score mapped to [0,1]
- Reward: partial for subset overlap, penalties for harmful misclassification

## 12) Pre-Submission Command Checklist

```bash
# 1) Local structure validation
openenv validate --verbose

# 2) Docker build and run
docker build -t email-triage-env:latest -f server/Dockerfile .
docker run -p 8000:8000 email-triage-env:latest

# 3) Runtime validation on local server
openenv validate --url http://localhost:8000

# 4) Baseline inference run
python inference.py

# 5) Push to HF Spaces
openenv push --repo-id <username>/<space-name>

# 6) Runtime validation on deployed space
openenv validate https://<username>-<space-name>.hf.space
```

## 13) Final Position

This submission can be executed mostly inside VS Code with local Docker iteration, then finalized via external HF deployment and API-backed baseline inference.

Best risk-adjusted path:

1. Start with deterministic, lightweight domain (email triage)
2. Build strict graders and shaped rewards first
3. Lock reproducible baseline script early
4. Treat validator checks as hard gates before deployment
