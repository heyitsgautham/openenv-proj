# Reusable Session Prompts

Use these three prompts for every session.
Only replace the placeholders:
- {SESSION_NUMBER}
- {SESSION_FILE}
- {TACTICAL_PLAN_FILE}

Example values for Session 1:
- {SESSION_NUMBER} = 1
- {SESSION_FILE} = hackathon/docs/sessions/01-session-kickoff-and-scaffold.md
- {TACTICAL_PLAN_FILE} = hackathon/docs/sessions-plan/session-01-tactical-plan.md

## 1. Plan Prompt

```text
You are a coding agent for OpenEnv environment development.
Read hackathon/docs/WINNING-PLAN.md, hackathon/docs/PS.md, and {SESSION_FILE}.
Work only on Session {SESSION_NUMBER}. Do not implement or edit code yet.
Create a tactical plan and save it to {TACTICAL_PLAN_FILE}.

Use ref-repos/OpenEnv only when needed to resolve framework-specific behavior.
If you use it, cite exact file paths consulted.
Do not explore unrelated repositories.

The tactical plan must include:
1. Scope and non-scope for this session.
2. Ordered implementation steps with target files.
3. Risks and mitigations.
4. Validation checklist mapped to this session file.
5. Exact verification commands and pass criteria.
6. Go or No-Go decision.
```

## 2. Execution Prompt

```text
Execute Session {SESSION_NUMBER} exactly as scoped in {SESSION_FILE} and {TACTICAL_PLAN_FILE}.
Precondition: {TACTICAL_PLAN_FILE} exists.

Use ref-repos/OpenEnv only if blocked on framework-specific behavior.
Do not broaden scope beyond this session.

Rules:
1. Do not start work from the next session.
2. Keep changes minimal and scoped to this session.
3. Do not modify files outside this session scope unless required for a direct dependency; if you do, justify it.
4. If blocked, report blocker and best fix path.
5. Run only the implementation and execution steps defined in the tactical plan.

After execution, report:
1. Files changed and why.
2. Commands run.
3. Any assumptions made.
4. Remaining blockers, if any.
```

## 3. Verification Prompt

```text
Verify whether all validations in {SESSION_FILE} and {TACTICAL_PLAN_FILE} are completed.
Run the required checks and report:
1. Pass or Fail for each checklist item.
2. Evidence lines from outputs.
3. If something fails, fix and re-run up to 3 focused attempts, then report final status and blockers.

End with a strict verdict:
Session {SESSION_NUMBER} Ready to move to next session or Not Ready.
```

## Optional Quick Mapping for All Sessions

- Session 1: hackathon/docs/sessions/01-session-kickoff-and-scaffold.md -> hackathon/docs/sessions-plan/session-01-tactical-plan.md
- Session 2: hackathon/docs/sessions/02-session-tasks-and-data.md -> hackathon/docs/sessions-plan/session-02-tactical-plan.md
- Session 3: hackathon/docs/sessions/03-session-graders-and-scoring-tests.md -> hackathon/docs/sessions-plan/session-03-tactical-plan.md
- Session 4: hackathon/docs/sessions/04-session-environment-loop-and-reward.md -> hackathon/docs/sessions-plan/session-04-tactical-plan.md
- Session 5: hackathon/docs/sessions/05-session-inference-baseline.md -> hackathon/docs/sessions-plan/session-05-tactical-plan.md
- Session 6: hackathon/docs/sessions/06-session-docker-and-local-validation.md -> hackathon/docs/sessions-plan/session-06-tactical-plan.md
- Session 7: hackathon/docs/sessions/07-session-deploy-and-submission.md -> hackathon/docs/sessions-plan/session-07-tactical-plan.md
