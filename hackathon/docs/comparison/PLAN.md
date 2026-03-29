# Hackathon Plan — OpenEnv Data Cleaning & Transformation Environment

**Author:** Claude Opus 4.6 (1M context)
**Date:** 2026-03-29

---

## Research Summary

Thorough analysis of:
- **OpenEnv spec** (ref-repos/OpenEnv) — full API, types, rubrics, MCP, validation, deployment patterns
- **Hackathon problem statement** (hackathon/docs/PS.md) — all requirements and evaluation criteria
- **Course modules 1–5** — complete patterns for building, deploying, and training with OpenEnv environments

---

## Domain Recommendation: Data Cleaning & Transformation

The agent receives messy real-world data + a specification, and must clean/transform it into correct structured output.

### Why This Domain?

| Evaluation Criteria | Weight | How This Scores |
|---------------------|--------|-----------------|
| Real-world utility | 30% | Every company does data cleaning daily — ETL, reporting, data entry, migration. Immediate value for agent evaluation. |
| Task & grader quality | 25% | Compare output field-by-field against ground truth. Fully deterministic. Clear difficulty progression. |
| Environment design | 20% | Per-row/per-field partial rewards, clean episode boundaries, sensible action/observation spaces. |
| Code quality & spec compliance | 15% | Standard OpenEnv 3-component pattern, typed Pydantic models, Dockerfile, openenv.yaml. |
| Creativity & novelty | 10% | Data cleaning is not a standard RL benchmark. Reward design based on multi-dimensional quality metrics. |

### Strengths

- **Massively practical** — data cleaning is one of the most common tasks in every organization
- **Deterministically gradable** — compare output against gold standard, field by field
- **Great partial rewards** — per-row accuracy, per-field correctness, format compliance, completeness
- **Zero external dependencies** — pure Python, no databases, no browsers, no APIs
- **Lightweight** — runs easily on the mandated 2 vCPU / 8GB RAM constraint
- **Novel** — not seen in existing RL/agent benchmarks

### Alternative Domains Considered

| Domain | Pros | Cons |
|--------|------|------|
| Incident Log Triage | Very practical for DevOps, clear grading | Needs realistic log data generation |
| Technical Support Tickets | Common task, good tool-use potential | Grading response quality is less deterministic |
| Configuration File Auditing | Novel, clear right/wrong answers | Narrower audience |
| Email Triage & Response | Classic example, well-understood | Less novel, response grading is subjective |
| SQL Query Optimization | Practical, measurable | Needs embedded database, heavier runtime |

---

## 3 Tasks with Difficulty Progression

### Task 1 — Easy: Basic Data Cleaning

**Objective:** Clean a CSV dataset with obvious quality issues.

**Issues to fix:**
- Missing values (empty cells, "N/A", "null" strings)
- Wrong data types (dates as strings, numbers with commas, booleans as "yes"/"no")
- Duplicate rows
- Inconsistent formatting (mixed case, trailing whitespace, inconsistent date formats)
- Out-of-range values (negative ages, future dates)

**Grading:** Per-field comparison against gold standard. Score = correct_fields / total_fields.

**Expected baseline score:** 0.6–0.8 (LLM should handle obvious issues well)

### Task 2 — Medium: Business Rule Transformation

**Objective:** Apply a set of business rules to transform raw data into a target schema.

**Operations required:**
- Categorize records based on multi-condition rules (e.g., "if revenue > 100K and region = 'US', category = 'Enterprise'")
- Compute derived fields (aggregations, lookups, conditional formulas)
- Validate cross-field constraints (e.g., "end_date must be after start_date")
- Merge/split columns according to specification
- Apply normalization rules (currency conversion, unit standardization)

**Grading:** Weighted composite — schema compliance (20%) + field accuracy (50%) + constraint satisfaction (30%). Score = weighted sum.

**Expected baseline score:** 0.3–0.5 (requires multi-step reasoning and rule application)

### Task 3 — Hard: Multi-Source Data Reconciliation

**Objective:** Reconcile conflicting data from 3 different sources with ambiguous specifications.

**Challenges:**
- Conflicting values across sources (different addresses, different amounts)
- Ambiguous merge keys (fuzzy matching on names, partial IDs)
- Missing specifications that must be inferred from context
- Priority rules that vary by field (Source A is authoritative for financials, Source B for contact info)
- Edge cases requiring judgment (how to handle records present in only 1 of 3 sources)

**Grading:** Multi-criteria — record matching accuracy (30%) + field-level correctness (30%) + conflict resolution quality (25%) + completeness (15%). Score = weighted sum.

**Expected baseline score:** 0.1–0.3 (genuinely challenging even for frontier models)

---

## Environment Architecture

### Action Space

```python
class DataCleanAction(Action):
    """What the agent sends each step."""
    operation: str          # "clean", "transform", "merge", "validate", "submit"
    target_field: Optional[str]    # Which column/field to operate on
    parameters: Dict[str, Any]     # Operation-specific params
    # e.g., {"operation": "fill_missing", "target_field": "email", "parameters": {"strategy": "infer_from_name"}}
```

Alternative: simpler approach where the agent submits the full cleaned dataset each step.

```python
class DataCleanAction(Action):
    """Agent submits current version of cleaned data."""
    data: List[Dict[str, Any]]     # The cleaned/transformed records
    done: bool = False             # Agent signals it's finished
```

### Observation Space

```python
class DataCleanObservation(Observation):
    """What the agent sees."""
    task_description: str                   # What needs to be done
    current_data: List[Dict[str, Any]]      # Current state of the data
    target_schema: Dict[str, Any]           # Expected output schema
    validation_errors: List[str]            # Current issues detected
    progress: float                         # 0.0–1.0 estimated progress
    # Inherited: done, reward, metadata
```

### State

```python
class DataCleanState(State):
    """Episode tracking."""
    task_id: str                    # Which task (easy/medium/hard)
    total_fields: int               # Total fields to clean
    correct_fields: int             # Currently correct fields
    # Inherited: episode_id, step_count
```

### Reward Function Design

```
reward = (
    0.4 * field_accuracy      +    # Per-field correctness (0.0–1.0)
    0.3 * completeness        +    # Fraction of records processed (0.0–1.0)
    0.2 * schema_compliance   +    # Output matches target schema (0.0–1.0)
    0.1 * efficiency_bonus         # Fewer steps = higher bonus (0.0–1.0)
)
```

**Partial progress signals at every step:**
- Each field fixed increases `field_accuracy`
- Each record processed increases `completeness`
- Schema violations decrease `schema_compliance`
- Destructive actions (deleting valid data) get penalized

**Penalizes undesirable behavior:**
- Submitting worse data than received (regression penalty)
- Infinite loops (same action repeated)
- Submitting without addressing known validation errors

---

## Project Structure

```
hackathon/data-cleaning-env/
├── __init__.py
├── models.py                        # Action, Observation, State (Pydantic)
├── client.py                        # EnvClient[DataCleanAction, DataCleanObservation, DataCleanState]
├── server/
│   ├── __init__.py
│   ├── environment.py               # DataCleanEnvironment(Environment) — core logic
│   ├── app.py                       # create_fastapi_app(DataCleanEnvironment)
│   ├── graders.py                   # Rubric classes for each task
│   ├── tasks/
│   │   ├── __init__.py
│   │   ├── easy.py                  # Task 1: basic cleaning
│   │   ├── medium.py                # Task 2: business rule transformation
│   │   ├── hard.py                  # Task 3: multi-source reconciliation
│   │   └── data/                    # Test datasets (JSON/CSV)
│   │       ├── easy_input.json
│   │       ├── easy_expected.json
│   │       ├── medium_input.json
│   │       ├── medium_rules.json
│   │       ├── medium_expected.json
│   │       ├── hard_source_a.json
│   │       ├── hard_source_b.json
│   │       ├── hard_source_c.json
│   │       └── hard_expected.json
│   └── Dockerfile
├── openenv.yaml                     # Environment manifest
├── pyproject.toml                   # Dependencies
├── inference.py                     # Baseline agent (OpenAI client, root directory)
└── README.md                        # Full documentation
```

---

## Implementation Phases

### Phase 0 — Domain Selection & Architecture Design

| | |
|---|---|
| **Where** | Claude Code (discussion) |
| **Effort** | ~30 min |
| **Output** | Finalized domain, types, task specs, reward design |

- Finalize the environment domain
- Design action/observation/state Pydantic models
- Design 3 tasks with concrete grading criteria
- Design reward function with partial progress signals
- Agree on project structure

### Phase 1 — Core Implementation

| | |
|---|---|
| **Where** | Entirely in Claude Code |
| **Effort** | Bulk of the work |
| **Output** | Working environment code |

Build the standard OpenEnv 3-component pattern:

1. **models.py** — Pydantic types for Action, Observation, State
2. **server/environment.py** — `reset()`, `step()`, `state()` with full game logic
3. **server/app.py** — `create_fastapi_app(DataCleanEnvironment)` wiring
4. **client.py** — `EnvClient` subclass with serialization
5. **server/tasks/** — Task definitions with test data generation
6. **server/graders.py** — Rubric classes producing 0.0–1.0 scores

### Phase 2 — Inference Script

| | |
|---|---|
| **Where** | Claude Code |
| **Depends on** | Phase 1 |
| **Output** | `inference.py` |

- Uses OpenAI client as mandated
- Reads `API_BASE_URL`, `MODEL_NAME`, `HF_TOKEN` from environment variables
- Runs baseline agent against all 3 tasks
- Produces reproducible scores
- Runtime < 20 min on vcpu=2, memory=8GB

### Phase 3 — Containerization & Configuration

| | |
|---|---|
| **Where** | Claude Code (writing files) |
| **Output** | Dockerfile, openenv.yaml, pyproject.toml, README.md |

- `Dockerfile` — multi-stage build following OpenEnv base image pattern
- `openenv.yaml` — spec version, name, type, runtime, app, port
- `pyproject.toml` — dependencies with `openenv-core>=0.2.0`, entry points
- `README.md` — environment description, motivation, action/observation space definitions, task descriptions, setup instructions, baseline scores

### Phase 4 — Local Testing & Validation

| | |
|---|---|
| **Where** | External environment (your terminal) |
| **Needs** | Docker, Python 3.10+, API keys |

- `docker build -t data-cleaning-env:latest -f server/Dockerfile .`
- `docker run -p 8000:8000 data-cleaning-env:latest`
- Hit endpoints: `/health`, `/schema`, `/metadata`, `/reset`, `/step`, `/state`
- Run `inference.py` — verify baseline scores on all 3 tasks
- Run `openenv validate` — verify spec compliance

### Phase 5 — HF Spaces Deployment

| | |
|---|---|
| **Where** | External environment |
| **Needs** | HF account + token |

- Create HF Space tagged with `openenv`
- Push code to Space repo
- Verify Space deploys and responds to `reset()`
- End-to-end smoke test from external client

### Phase 6 — Final Validation & Polish

| | |
|---|---|
| **Where** | Claude Code + external |
| **Output** | Submission-ready environment |

- Run the full pre-submission checklist from PS.md
- Verify all 5 automated gates pass
- Polish README with actual baseline scores
- Final code review

---

## What Can vs. Cannot Be Done in Claude Code

| Phase | In Claude Code? | External Needs |
|-------|----------------|----------------|
| 0. Design | Yes | None |
| 1. Core code | **Yes** | None |
| 2. Inference script | **Yes** (writing) | API keys to run |
| 3. Docker/config files | **Yes** (writing) | Docker daemon to build |
| 4. Local testing | **Partially** | Docker + Python env + API keys |
| 5. HF deployment | **No** | HF account, token, git push |
| 6. Final validation | **Partially** | Running server + openenv CLI |

**~80% of the work (all code, config, docs) happens in Claude Code.**
**~20% needs your local terminal for Docker, server testing, and HF deployment.**

---

## External Requirements

| Requirement | Purpose |
|-------------|---------|
| Python 3.10+ | Runtime |
| `uv` | Dependency management, lock file generation |
| Docker | Container build and test |
| HF Account + Token | Spaces deployment |
| API key (`API_BASE_URL`, `MODEL_NAME`, `HF_TOKEN`) | Running inference script |
| `openenv-core` package | Validation CLI |

---

## Tools, MCPs, and Skills Needed

| Tool/Skill | Purpose | Where |
|------------|---------|-------|
| Claude Code (Read, Write, Edit, Grep, Glob) | All code writing and editing | In-session |
| `/commit` skill | Git commits at milestones | In-session |
| `/pr` skill | GitHub PR if pushing to remote | In-session |
| `Explore` agents | Referencing OpenEnv patterns from ref-repos during implementation | In-session |
| Docker CLI | Build + test container | Your terminal |
| `uvicorn` | Local server testing | Your terminal |
| `openenv validate` | Pre-submission validation | Your terminal |
| HF CLI / `openenv push` | Deploy to Spaces | Your terminal |

**No special MCP servers are required.** The environment is self-contained with no external service dependencies.

---

## Key Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| `openenv-core` API differences from course examples | Broken imports, wrong base classes | Validate against ref-repos/OpenEnv source code, not just course text |
| Inference script timeout (>20 min) | Disqualification | Design tasks with bounded data sizes; limit max steps |
| Graders not deterministic | Score variance check fails (Phase 2 judging) | Use exact field comparison, no floating-point tolerance issues |
| Docker base image unavailable | Build fails | Provide fallback `FROM python:3.11-slim` Dockerfile |
| Reward function too sparse | Poor agent learning signal | Ensure per-step partial rewards, not just end-of-episode |

---

## Success Criteria (Pre-Submission Checklist)

- [ ] HF Space deploys and returns 200 + responds to `reset()`
- [ ] `openenv validate` passes (openenv.yaml, typed models, step/reset/state endpoints)
- [ ] `docker build && docker run` works cleanly
- [ ] `inference.py` completes without error, produces scores on all 3 tasks
- [ ] 3 tasks with graders, all scores in 0.0–1.0 range
- [ ] README with environment description, action/observation spaces, task descriptions, setup instructions, baseline scores
