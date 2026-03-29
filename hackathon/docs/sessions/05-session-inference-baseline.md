# Session 5: Inference Baseline and Robust Connection Logic

Estimated effort: 2-3 hours

## Goal
Implement root inference.py with OpenAI client, robust credential handling, and dual-mode environment connection.

## Inputs
- Session 4 output
- hackathon/docs/WINNING-PLAN.md (Section 7)

## Tactical Plan Output (Plan Prompt Artifact)
- hackathon/docs/sessions-plan/session-05-tactical-plan.md

## Mandatory Workflow
1. Plan first.
2. Save the tactical plan to the Tactical Plan Output file.
3. Implement/execute using both this session spec and the tactical plan.
4. Verify against checks from both this session spec and the tactical plan.
5. Report artifacts and blockers.

## Step 1: Plan First
Plan should include:
- Prompt format and parsing strategy.
- Credential fallback order.
- Connection fallback order (ENV_URL first, Docker fallback).
- Task loop limits and early-stop rules.

Do not implement before this is written.
The plan must be saved to the Tactical Plan Output file.

## Step 2: Implement and Execute
Implement:

Precondition: Tactical Plan Output file exists.

- hackathon/data_cleaning_env/inference.py

Requirements:
- Use OpenAI Python client only.
- API key fallback: HF_TOKEN, API_KEY, OPENAI_API_KEY.
- Connection function uses ENV_URL first and asyncio.run(from_docker_image()) fallback.
- Runs all three tasks and prints per-task and average scores.

## Step 3: Verify
Run:

```bash
cd hackathon/data_cleaning_env
python -m compileall inference.py
rg -n "from openai import OpenAI|HF_TOKEN|API_KEY|OPENAI_API_KEY|ENV_URL|DOCKER_IMAGE|asyncio.run\(" inference.py
python inference.py
```

If real model credentials are unavailable, run and verify fail-fast messages are clear and intentional.

Verification must confirm:
- Script starts and validates env vars correctly.
- No hardcoded secrets.
- Control flow supports both evaluator connection scenarios.
- All checks defined in the tactical plan are completed.

## Deliverables
- Final inference.py at package root.
- Verification notes including credential and connection behavior.

## Done Criteria
- Inference script is evaluator-safe and reproducible.
- No connection ambiguity remains.
