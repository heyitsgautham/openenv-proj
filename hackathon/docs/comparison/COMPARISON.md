# Head-to-Head Analysis: Claude Opus 4.6 vs Codex-5.3-max

**Date:** 2026-03-29
**Files compared:**
- `hackathon/docs/PLAN.md` (Claude Opus 4.6, 1M context)
- `hackathon/docs/openenv-hackathon-approach.md` (Codex-5.3-max)

---

## Scoring Summary

| Dimension | Opus 4.6 | Codex-5.3-max | Winner |
|-----------|:---:|:---:|:---:|
| Research transparency | 6/10 | **9/10** | **Codex** |
| Domain choice | **8/10** | 6/10 | **Opus** |
| Technical specificity | **9/10** | 5/10 | **Opus** |
| Validator/spec awareness | 6/10 | **9/10** | **Codex** |
| Task design depth | **9/10** | 5/10 | **Opus** |
| Risk analysis | 7/10 | **8/10** | **Codex** |
| Actionability (can I start building now?) | **8/10** | 7/10 | **Opus** |
| Phase planning | 7/10 | **8/10** | **Codex** |
| Reward function design | **9/10** | 4/10 | **Opus** |
| Pre-submission readiness | 6/10 | **9/10** | **Codex** |

---

## Detailed Breakdown

### 1. Research Transparency — Codex wins decisively

Codex Section 3 cites **27 specific files** it read — validator internals, rubric patterns, inference examples (`finqa_inference.py`, `coding_env_inference.py`), RFC docs. Every claim can be traced to a source file. Opus says "thorough analysis of ref-repos/OpenEnv" without listing specific files. This matters because if something is wrong, you can't verify where the claim originated.

### 2. Domain Choice — Opus wins

- **Opus (Data Cleaning & Transformation):** Higher novelty score, richer action space, more natural difficulty progression, and better reward shaping potential. The hard task (multi-source reconciliation) genuinely challenges frontier models.
- **Codex (Email Triage):** Safer, more conventional choice. The PS.md literally lists email triage as an example domain — judges will see it as "the obvious pick." The easy task (spam/ham binary classification) is essentially a solved problem and may feel too trivial. Less creativity/novelty points (10% weight in evaluation).

Notably, Codex lists "Data cleaning and validation" as a backup option, ranking it below email triage. Opus ranked email triage as less novel in its alternatives table. Both identified the same candidate pool but made opposite bets.

### 3. Technical Specificity — Opus wins clearly

Opus includes:
- Actual Python code for Action, Observation, State models (two alternative Action designs)
- Explicit reward function formula with weights (`0.4 * field_accuracy + 0.3 * completeness + ...`)
- Full directory tree down to individual data files (`easy_input.json`, `hard_source_a.json`, etc.)
- Expected baseline scores per task (0.6–0.8, 0.3–0.5, 0.1–0.3)

Codex's task blueprint (Section 11) is 3 bullet points per task with no code, no models, no reward formula. You couldn't start implementing from Section 11 alone.

### 4. Validator/Spec Awareness — Codex wins clearly

Codex Section 9 lists the **exact validation checks** the OpenEnv CLI performs:

- **Local:** `pyproject.toml`, `uv.lock`, script entrypoint, `server/app.py` main()
- **Runtime:** `/openapi.json`, `/health`, `/metadata`, `/schema`, `/mcp`, endpoint-mode consistency

Opus mentions `openenv validate` as a step to run but doesn't document what it actually checks. Codex also references `finqa_env/server/rewards.py` and `repl_env/rubrics.py` as real-world grading patterns — showing it studied existing environments' actual reward code, not just the framework abstractions.

### 5. Task Design — Opus wins

| | Opus | Codex |
|---|---|---|
| Easy task | 5 specific issue types listed, per-field grading formula | "Binary spam/ham classification" — one sentence |
| Medium task | 5 specific operations, weighted composite score breakdown (20/50/30) | "Priority ranking" — one sentence |
| Hard task | 5 specific challenges, 4-component grading weights (30/30/25/15) | "Multi-label decision" — one sentence |
| Baseline scores | Predicted per task | Not mentioned |

Opus tasks are implementation-ready. Codex tasks are conceptual outlines that need a second design pass before coding can begin.

### 6. Risk Analysis — Codex wins slightly

Both identify similar risks (constant graders, sparse rewards, Docker failures). Codex adds two that Opus missed:

- **State leakage across resets** — specific to environment correctness, not just deployment
- **Hardcoded model settings in inference** — specific to disqualification risk

Opus includes a risk about "Docker base image unavailable" with a fallback to `python:3.11-slim`, which is a practical detail Codex doesn't cover. Overall close, but Codex's risks are more operational and disqualification-focused.

### 7. Phase Planning — Codex wins slightly

Codex provides:
- **Time estimates** per phase (0.5 day, 1–1.5 days, etc.) — totaling ~5.5–7.5 days
- **Validation gates** at every phase boundary ("reward distribution is non-constant", "easy scores higher than hard")
- **Exact CLI commands** to run at each phase (`openenv init`, `openenv validate --url`, `openenv push`)
- Mentions `openenv init` for scaffolding — a real CLI command that saves setup time

Opus phases have clearer output/location mapping (table per phase showing where work happens) but lack time estimates, and the per-phase validation gates are less explicit.

### 8. Reward Function — Opus wins decisively

Opus gives a concrete formula:
```
reward = 0.4 * field_accuracy + 0.3 * completeness + 0.2 * schema_compliance + 0.1 * efficiency_bonus
```

Plus per-step partial signals, regression penalties, and anti-loop mechanics.

Codex mentions "partial progress reward and penalties" and "+1 correct, 0 incorrect, small step penalty" but never defines how rewards compose or what the shaping curve looks like. For a hackathon where environment design (including reward) is 20% of the grade, this gap matters.

### 9. Pre-Submission Readiness — Codex wins

Codex Section 12 is a **copy-paste-ready bash script** with 6 numbered steps covering local validation through deployed validation. Section 4 cleanly separates functional vs non-functional vs disqualification-risk checklist items.

Opus has a success criteria checkbox list but lacks the concrete commands and the disqualification-risk separation.

### 10. MCP Stance — Codex is more explicit

Codex dedicates Section 8 to answering "Do We Need MCP?" with a clear **no** and explains why. Opus states "No special MCP servers are required" but buries it in a tools table rather than addressing the architectural question directly.

---

## What Each Plan is Missing

### Opus is missing

- Explicit source citations (which files were read during research)
- Validator check details (what `openenv validate` actually tests)
- Time estimates per phase
- Per-phase validation gates (pass/fail criteria between phases)
- `openenv init` CLI mention for scaffolding
- Specific env var default values (Codex gives `API_BASE_URL` default)
- References to existing environment reward implementations (finqa, repl_env)
- Explicit MCP decision section

### Codex is missing

- Any Python code (zero code snippets in the entire document)
- Reward function formula or component weights
- Action/Observation/State type definitions
- Expected baseline scores per task
- Detailed task specifications (what specifically the agent must do at each difficulty level)
- Project directory structure with file-level detail
- Alternative Action design considerations
- Domain comparison table with pros/cons for each candidate
- Architecture diagram or model relationships

---

## Structural Comparison

| Aspect | Opus | Codex |
|--------|------|-------|
| Sections | 12 sections | 13 sections |
| Lines | 372 | 361 |
| Code snippets | 6 (Python models, reward formula, directory tree) | 3 (bash commands only) |
| Tables | 9 | 0 (uses lists throughout) |
| Domain alternatives | 5 candidates compared with pros/cons | 3 backups listed without analysis |
| Source citations | 0 specific files | 27 specific files |
| Time estimates | None | Per-phase (0.5–1.5 days each) |
| Validation gates | End-of-plan checklist | Per-phase gates |

---

## Bottom Line

**Codex-5.3-max wrote a better project manager's plan** — rigorous compliance tracking, source transparency, validation gates at every phase, time estimates, and a "don't get disqualified" focus. It's the plan you'd hand to someone who needs to stay on rails and avoid failure modes.

**Opus 4.6 wrote a better architect's plan** — concrete types, reward math, task design depth, alternative design explorations, and implementation-ready detail. It's the plan you'd hand to someone who needs to start coding now.

**If building this for real, the optimal approach would merge both:** use Codex's validator awareness, source citations, phase gates, and pre-submission checklist, combined with Opus's domain choice, type definitions, reward formula, and task specifications. The two plans are surprisingly complementary — their strengths and weaknesses barely overlap.
