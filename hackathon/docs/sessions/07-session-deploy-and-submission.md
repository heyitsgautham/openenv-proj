# Session 7: HF Deployment, Live Smoke Test, and Submission Readiness

Estimated effort: 2-3 hours

## Goal
Deploy to Hugging Face Space, validate remotely, run live smoke test, and finalize submission artifacts.

## Inputs
- Session 6 output
- hackathon/docs/WINNING-PLAN.md (submission structure and checklist)

## Tactical Plan Output (Plan Prompt Artifact)
- hackathon/docs/sessions-plan/session-07-tactical-plan.md

## Mandatory Workflow
1. Plan first.
2. Save the tactical plan to the Tactical Plan Output file.
3. Implement/execute using both this session spec and the tactical plan.
4. Verify against checks from both this session spec and the tactical plan.
5. Report final readiness and residual risk.

## Step 1: Plan First
Plan should include:
- Deployment command sequence.
- Remote validation sequence.
- Live smoke test method against Space URL.
- Final checklist closure approach.

Do not deploy before this plan is written.
The plan must be saved to the Tactical Plan Output file.

## Step 2: Implement and Execute
Run:

Precondition: Tactical Plan Output file exists.

```bash
cd hackathon/data_cleaning_env
openenv push --repo-id <username>/data-cleaning-env
openenv validate https://<username>-data-cleaning-env.hf.space
python -c "from data_cleaning_env import DataCleanEnv; env=DataCleanEnv(base_url='https://<username>-data-cleaning-env.hf.space').sync(); r=env.reset(task_id='easy'); print(len(r.observation.input_data)); env.close()"
python inference.py
```

Then finalize README with baseline scores and required sections.

## Step 3: Verify
Verification must confirm:
- Space is reachable and healthy.
- Remote validation passes.
- Live reset smoke test works against Space URL directly.
- Baseline scores are recorded in README.
- All checks defined in the tactical plan are completed.

## Deliverables
- Deployed HF Space URL.
- Final GitHub submission repo URL.
- Completed pre-submission checklist.
- Final run log summary.

## Done Criteria
- All required submission artifacts exist and are validated.
- No unresolved blocker for submission.
