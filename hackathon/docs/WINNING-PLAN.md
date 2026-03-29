# Definitive Winning Plan — OpenEnv Hackathon

**Merged from:** Claude Opus 4.6 (PLAN.md) + Codex-5.3-max (openenv-hackathon-approach.md)
**Verified against:** ref-repos/OpenEnv source code, CLI templates, validator internals, existing env implementations
**Revised:** Incorporates all issues identified by Codex-5.3-max review (credentials, Docker dependency, step limits, prompt truncation, loop penalties)
**Date:** 2026-03-29

---

## Table of Contents

1. [Strategy & Scoring Target](#1-strategy--scoring-target)
2. [Domain: Data Cleaning & Transformation](#2-domain-data-cleaning--transformation)
3. [Three Tasks — Full Specification](#3-three-tasks--full-specification)
4. [Architecture — Verified Code Patterns](#4-architecture--verified-code-patterns)
5. [Reward System Design](#5-reward-system-design)
6. [File-by-File Implementation Guide](#6-file-by-file-implementation-guide)
7. [Inference Script — Exact Pattern](#7-inference-script--exact-pattern)
8. [Phased Execution with Validation Gates](#8-phased-execution-with-validation-gates)
9. [Validator Compliance — Hard Requirements](#9-validator-compliance--hard-requirements)
10. [Failure Modes & Mitigations](#10-failure-modes--mitigations)
11. [External Dependencies & Environment Setup](#11-external-dependencies--environment-setup)
12. [Pre-Submission Checklist](#12-pre-submission-checklist)
13. [Submission Structure — Repo Layout](#13-submission-structure--repo-layout)
14. [Resolved Ambiguities from PS.md](#14-resolved-ambiguities-from-psmd)
15. [Research Sources](#15-research-sources)

---

## 1. Strategy & Scoring Target

### Evaluation Weights (from PS.md)

| Criteria | Weight | Our Target | How We Win |
|----------|--------|------------|------------|
| Real-world utility | 30% | 26–30/30 | Data cleaning is a universal task — every company, every day |
| Task & grader quality | 25% | 20–25/25 | Deterministic field-level grading, clear difficulty curve, predicted baseline scores |
| Environment design | 20% | 16–20/20 | Per-step partial rewards, clean resets, well-typed action/observation spaces |
| Code quality & spec compliance | 15% | 12–15/15 | Canonical OpenEnv patterns, passes `openenv validate`, Docker builds clean |
| Creativity & novelty | 10% | 7–10/10 | Data cleaning not seen in existing OpenEnv envs or standard RL benchmarks |

### Three Judging Phases We Must Survive

1. **Automated Validation (pass/fail gate):** HF Space deploys, spec compliance, Dockerfile builds, baseline reproduces, 3+ tasks with graders
2. **Agentic Evaluation (scored):** Standard LLM agent run against our environment — reward must provide useful signal, not just binary
3. **Human Review (scored):** Meta + HF engineers assess real-world utility, creativity, exploit resistance

---

## 2. Domain: Data Cleaning & Transformation

### What It Is

The agent receives messy, real-world-style tabular data plus a task specification, and must produce clean, correctly structured output. The environment simulates what data engineers, analysts, and ops teams do daily.

### Why This Domain Wins

- **Universally practical:** Every organization has data cleaning workflows — ETL, reporting, migration, compliance
- **Deterministically gradable:** Compare agent output field-by-field against gold standard — no subjectivity
- **Rich partial rewards:** Per-row accuracy, per-field correctness, schema compliance, completeness — all computable every step
- **Zero external dependencies:** Pure Python, no databases, no browsers, no network calls from environment
- **Lightweight runtime:** Runs easily on 2 vCPU / 8GB RAM
- **Novel:** Not seen in existing OpenEnv environments (`echo_env`, `coding_env`, `finqa_env`, `repl_env`, `browsergym_env`) or standard RL benchmarks
- **Exploit-resistant:** Gold standard is hidden server-side; agent only sees validation errors, not the answer

### Why Not Email Triage (Codex's Pick)

- PS.md literally lists "email triage" as an example domain — judges will see it as the obvious/safe pick (lower novelty score)
- Spam/ham binary classification (Codex's easy task) is a solved problem — too trivial
- Response quality grading for email is inherently less deterministic than field-level data comparison
- Data cleaning has richer action space and more natural difficulty progression

---

## 3. Three Tasks — Full Specification

### Task 1 — Easy: Basic Data Cleaning

**Objective:** Clean a 50-row CSV dataset with obvious quality issues.

**Input data issues (planted):**
- Missing values: empty cells, "N/A", "null", "none", "–" strings
- Wrong types: dates as `"March 5 2024"` instead of `2024-03-05`, numbers with `$` or `,`, booleans as `"yes"`/`"no"`
- Duplicate rows (3–5 exact duplicates)
- Formatting: mixed case in categories (`"active"`, `"Active"`, `"ACTIVE"`), trailing whitespace, inconsistent phone formats
- Out-of-range: negative ages, dates in the future, email without `@`

**Target schema:** 8 columns (name, email, phone, date_of_birth, status, amount, category, notes)

**Grading formula:**
```
score = correct_fields / total_fields
```
Simple per-field exact match against gold standard after normalization.

**Expected baseline score:** 0.6–0.8 (frontier LLMs handle obvious issues well)

**Max steps:** 10

---

### Task 2 — Medium: Business Rule Transformation

**Objective:** Transform 100 rows of raw transaction data by applying a set of explicit business rules.

**Rules the agent must apply:**
1. **Categorize:** If `amount > 10000` AND `region == "US"` → `tier = "Enterprise"`, else if `amount > 1000` → `tier = "Business"`, else `tier = "Personal"`
2. **Compute derived fields:** `tax = amount * tax_rate[region]`, `total = amount + tax`
3. **Validate constraints:** `end_date > start_date`, `email` matches regex, `quantity > 0`
4. **Normalize:** Convert all currencies to USD using provided rate table, standardize date format to ISO 8601
5. **Merge columns:** Combine `first_name` + `last_name` → `full_name`, split `address` into `street`, `city`, `state`, `zip`

**Input:** Raw data JSON + rules specification JSON + reference tables JSON (tax rates, currency rates)

**Grading formula:**
```
score = 0.2 * schema_compliance + 0.5 * field_accuracy + 0.3 * constraint_satisfaction
```
- `schema_compliance`: Does output have all required columns with correct types? (0.0 or 1.0)
- `field_accuracy`: Per-field comparison with tolerance for numerics (0.0–1.0)
- `constraint_satisfaction`: Fraction of cross-field constraints met (0.0–1.0)

**Expected baseline score:** 0.3–0.5 (requires multi-step reasoning + rule application)

**Max steps:** 15

---

### Task 3 — Hard: Multi-Source Data Reconciliation

**Objective:** Reconcile conflicting customer records from 3 different source systems into a single golden record set.

**Challenges:**
- **Conflicting values:** Source A says address is "123 Main St", Source B says "123 Main Street", Source C says "124 Main St"
- **Ambiguous merge keys:** Names differ slightly (`"John Smith"` vs `"J. Smith"` vs `"Jonathan Smith"`), partial ID overlap
- **Source priority rules (provided):** Source A is authoritative for financials, Source B for contact info, Source C for metadata — but rules have exceptions
- **Missing data:** Some records appear in only 1 or 2 of 3 sources
- **Inference required:** Some specs are ambiguous — agent must infer intent from context and examples

**Input:** 3 source JSON files (40-60 records each, ~30 overlapping entities) + reconciliation spec + priority rules

**Grading formula:**
```
score = 0.30 * record_matching + 0.30 * field_correctness + 0.25 * conflict_resolution + 0.15 * completeness
```
- `record_matching`: Did agent correctly identify which records across sources refer to the same entity? (0.0–1.0)
- `field_correctness`: For matched records, are the golden values correct? (0.0–1.0)
- `conflict_resolution`: When sources conflict, did agent apply priority rules correctly? (0.0–1.0)
- `completeness`: Fraction of expected output records present (0.0–1.0)

**Expected baseline score:** 0.1–0.3 (genuinely hard — fuzzy matching + rule application + inference)

**Max steps:** 20

---

## 4. Architecture — Verified Code Patterns

All patterns below are verified against the actual OpenEnv source code and CLI templates.

### 4.1 Models (`models.py`)

Based on: `ref-repos/OpenEnv/src/openenv/core/env_server/types.py`, `ref-repos/OpenEnv/docs/environment-builder.md`

```python
from typing import Any, Dict, List, Optional
from pydantic import Field
from openenv.core.env_server.types import Action, Observation, State


class DataCleanAction(Action):
    """Agent submits its current version of the cleaned/transformed data."""
    data: List[Dict[str, Any]] = Field(
        ..., description="The cleaned/transformed records"
    )


class DataCleanObservation(Observation):
    """What the agent sees after each step."""
    task_description: str = Field(
        default="", description="Natural language description of the task"
    )
    input_data: List[Dict[str, Any]] = Field(
        default_factory=list, description="The raw input data to clean"
    )
    target_schema: Dict[str, Any] = Field(
        default_factory=dict, description="Expected output schema definition"
    )
    validation_errors: List[str] = Field(
        default_factory=list, description="Current issues detected in submitted data"
    )
    current_score: float = Field(
        default=0.0, description="Current grading score (0.0-1.0)"
    )
    # Inherited from Observation: done, reward, metadata


class DataCleanState(State):
    """Episode tracking state."""
    task_id: str = Field(default="easy", description="Current task identifier")
    total_fields: int = Field(default=0, ge=0, description="Total gradable fields")
    correct_fields: int = Field(default=0, ge=0, description="Currently correct fields")
    max_steps: int = Field(default=10, description="Maximum steps for this task")
    # Inherited from State: episode_id, step_count
```

### 4.2 Environment (`server/data_cleaning_environment.py`)

Based on: `ref-repos/OpenEnv/src/openenv/core/env_server/interfaces.py`, `ref-repos/OpenEnv/envs/coding_env/server/`, `ref-repos/OpenEnv/cli/templates/openenv_env/server/`

```python
from uuid import uuid4
from typing import Optional
from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

from ..models import DataCleanAction, DataCleanObservation, DataCleanState
from .graders import grade_submission
from .tasks import TASK_REGISTRY


class DataCleanEnvironment(Environment):
    """Data Cleaning & Transformation environment."""

    SUPPORTS_CONCURRENT_SESSIONS = True

    def __init__(self):
        self._state = DataCleanState(episode_id=str(uuid4()), step_count=0)
        self._task = None
        self._best_score = 0.0
        self._previous_score = 0.0
        self._last_action_hash = None       # Loop detection
        self._no_progress_streak = 0        # Stagnation detection

    def reset(
        self,
        seed: Optional[int] = None,
        episode_id: Optional[str] = None,
        **kwargs,
    ) -> DataCleanObservation:
        task_id = kwargs.get("task_id", "easy")
        task = TASK_REGISTRY[task_id]
        self._task = task
        self._best_score = 0.0
        self._previous_score = 0.0
        self._last_action_hash = None
        self._no_progress_streak = 0
        self._state = DataCleanState(
            episode_id=episode_id or str(uuid4()),
            step_count=0,
            task_id=task_id,
            total_fields=task.total_gradable_fields,
            correct_fields=0,
            max_steps=task.max_steps,
        )
        return DataCleanObservation(
            task_description=task.description,
            input_data=task.input_data,
            target_schema=task.target_schema,
            validation_errors=[],
            current_score=0.0,
            done=False,
            reward=0.0,
            metadata={"task_id": task_id, "step": 0},
        )

    def step(
        self,
        action: DataCleanAction,
        timeout_s: Optional[float] = None,
        **kwargs,
    ) -> DataCleanObservation:
        self._state.step_count += 1
        step = self._state.step_count

        # Grade the submission
        result = grade_submission(self._task, action.data)
        score = result.score
        errors = result.errors
        correct = result.correct_fields

        # Update state
        self._state.correct_fields = correct

        # --- Loop detection (PS.md requires penalizing infinite loops) ---
        action_hash = hash(str(sorted(str(r) for r in action.data)))
        is_repeat = action_hash == self._last_action_hash
        self._last_action_hash = action_hash

        # Stagnation detection: no score improvement for N consecutive steps
        if abs(score - self._previous_score) < 0.001:
            self._no_progress_streak += 1
        else:
            self._no_progress_streak = 0

        # --- Reward computation ---
        improvement = max(0.0, score - self._previous_score)
        regression_penalty = max(0.0, self._previous_score - score) * 0.5
        repeat_penalty = 0.15 if is_repeat else 0.0
        stagnation_penalty = min(0.1 * self._no_progress_streak, 0.3)

        reward = (
            0.50 * score                  # Absolute quality
            + 0.25 * improvement          # Progress reward
            - 0.10 * regression_penalty   # Don't make things worse
            - repeat_penalty              # Don't repeat exact same action
            - stagnation_penalty          # Don't stall
        )
        reward = max(0.0, min(1.0, reward))

        self._previous_score = score
        self._best_score = max(self._best_score, score)

        # Episode termination
        is_done = step >= self._state.max_steps or score >= 0.99

        return DataCleanObservation(
            task_description=self._task.description,
            input_data=self._task.input_data,
            target_schema=self._task.target_schema,
            validation_errors=errors,
            current_score=score,
            done=is_done,
            reward=reward,
            metadata={
                "task_id": self._state.task_id,
                "step": step,
                "best_score": self._best_score,
                "correct_fields": correct,
                "total_fields": self._state.total_fields,
            },
        )

    @property
    def state(self) -> DataCleanState:
        return self._state

    def get_metadata(self):
        from openenv.core.env_server.types import EnvironmentMetadata
        return EnvironmentMetadata(
            name="data_cleaning_env",
            description="Data Cleaning & Transformation environment for AI agents",
            version="0.1.0",
        )
```

### 4.3 Server App (`server/app.py`)

**Exact canonical pattern** from: `ref-repos/OpenEnv/src/openenv/cli/templates/openenv_env/server/app.py`

```python
"""FastAPI application for Data Cleaning Environment."""

try:
    from openenv.core.env_server.http_server import create_app
except Exception as e:
    raise ImportError(
        "openenv is required. Install dependencies with 'uv sync'"
    ) from e

try:
    from ..models import DataCleanAction, DataCleanObservation
    from .data_cleaning_environment import DataCleanEnvironment
except ModuleNotFoundError:
    from models import DataCleanAction, DataCleanObservation
    from server.data_cleaning_environment import DataCleanEnvironment


app = create_app(
    DataCleanEnvironment,        # Pass CLASS, not instance
    DataCleanAction,             # Action type class
    DataCleanObservation,        # Observation type class
    env_name="data_cleaning_env",
    max_concurrent_envs=1,
)


def main(host: str = "0.0.0.0", port: int = 8000):
    """Entry point for direct execution via uv run or python -m."""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    main(port=args.port)
```

**Critical notes (from verified source):**
- `create_app()` signature: `env: Callable[[], Environment]` — pass the **class**, not an instance
- Both `action_cls` and `observation_cls` are **Type** parameters
- `main()` function is **required** — validator checks for `def main(` in `server/app.py`
- `if __name__` block is **required** — validator checks for it

### 4.4 Client (`client.py`)

Based on: `ref-repos/OpenEnv/src/openenv/core/env_client.py`, `ref-repos/OpenEnv/envs/coding_env/client.py`

```python
"""Client for Data Cleaning Environment."""

from openenv.core.env_client import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State

from .models import DataCleanAction, DataCleanObservation, DataCleanState


class DataCleanEnv(EnvClient[DataCleanAction, DataCleanObservation, DataCleanState]):
    """Client for interacting with the Data Cleaning environment."""

    def _step_payload(self, action: DataCleanAction) -> dict:
        return {"data": action.data}

    def _parse_result(self, payload: dict) -> StepResult[DataCleanObservation]:
        obs_data = payload.get("observation", {})
        obs = DataCleanObservation(
            task_description=obs_data.get("task_description", ""),
            input_data=obs_data.get("input_data", []),
            target_schema=obs_data.get("target_schema", {}),
            validation_errors=obs_data.get("validation_errors", []),
            current_score=obs_data.get("current_score", 0.0),
            done=payload.get("done", False),
            reward=payload.get("reward"),
            metadata=obs_data.get("metadata", {}),
        )
        return StepResult(
            observation=obs,
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: dict) -> DataCleanState:
        return DataCleanState(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
            task_id=payload.get("task_id", "easy"),
            total_fields=payload.get("total_fields", 0),
            correct_fields=payload.get("correct_fields", 0),
            max_steps=payload.get("max_steps", 10),
        )
```

### 4.5 Graders (`server/graders.py`)

Based on: `ref-repos/OpenEnv/envs/repl_env/rubrics.py`, `ref-repos/OpenEnv/envs/finqa_env/server/rewards.py`, `ref-repos/OpenEnv/src/openenv/core/rubrics/base.py`

```python
"""Grading logic for data cleaning tasks."""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class GradeResult:
    score: float               # 0.0–1.0
    correct_fields: int
    total_fields: int
    errors: List[str] = field(default_factory=list)


def grade_submission(task, submitted_data: List[Dict[str, Any]]) -> GradeResult:
    """Grade agent's submitted data against the task's gold standard."""
    return task.grade(submitted_data)


def compare_field(expected: Any, actual: Any, field_type: str = "string") -> bool:
    """Compare a single field value with type-aware tolerance.

    Based on pattern from finqa_env/server/rewards.py:
    - Numeric: check BOTH relative error AND absolute difference
    - String: normalize then exact match
    - Date: parse to ISO then compare
    """
    if expected is None and actual is None:
        return True
    if expected is None or actual is None:
        return False

    if field_type == "numeric":
        try:
            exp_num = float(str(expected).replace(",", "").replace("$", ""))
            act_num = float(str(actual).replace(",", "").replace("$", ""))
            if exp_num == 0:
                return abs(act_num) < 0.001
            abs_diff = abs(exp_num - act_num)
            rel_error = abs_diff / abs(exp_num)
            return rel_error <= 0.01 and abs_diff <= 1.0
        except (ValueError, TypeError):
            return False

    # String comparison: normalize whitespace, case, strip
    exp_str = str(expected).strip().lower()
    act_str = str(actual).strip().lower()
    return exp_str == act_str
```

---

## 5. Reward System Design

### Composite Reward Formula

```
reward_per_step = (
    0.50 * absolute_score        # Current overall quality (0.0–1.0)
  + 0.25 * improvement           # Improvement over previous step (>= 0.0)
  - 0.10 * regression_penalty    # Penalty for making things worse (>= 0.0)
  - repeat_penalty               # 0.15 if exact same action repeated, else 0.0
  - stagnation_penalty           # 0.1 per consecutive no-progress step, capped at 0.3
)
clamped to [0.0, 1.0]
```

### Explicit Undesirable Behavior Penalties (Required by PS.md line 41)

| Behavior | Detection | Penalty |
|----------|-----------|---------|
| **Repeated identical action** (infinite loop) | Hash current action, compare to previous | -0.15 per repeat |
| **No progress stagnation** | Score unchanged for N consecutive steps | -0.1 × N (capped at -0.3) |
| **Regression** (making data worse) | Current score < previous score | -0.05 × (previous - current) |
| **Empty submission** | Submitted data is empty list | Score = 0.0 (natural consequence) |

### Why This Works for Each Judging Phase

- **Phase 2 (Agentic Evaluation):** Standard LLM agent gets useful gradient signal at every step — not just sparse terminal reward. Improvement term rewards incremental progress. Loop/stagnation penalties prevent degenerate trajectories.
- **Phase 3 (Human Review):** Reward clearly maps to meaningful task progress. Explicit loop penalties address PS.md requirement. No gaming possible since gold standard is server-side.

### Per-Task Scoring Components

| Component | Task 1 (Easy) | Task 2 (Medium) | Task 3 (Hard) |
|-----------|---------------|------------------|----------------|
| Primary metric | `correct_fields / total_fields` | Weighted composite (schema 20% + accuracy 50% + constraints 30%) | Multi-criteria (matching 30% + fields 30% + conflicts 25% + completeness 15%) |
| Partial credit | Per-field | Per-field + per-rule | Per-entity + per-field + per-conflict |
| Anti-gaming | Gold standard hidden | Rules provided but edge cases test understanding | Ambiguous specs require inference |

### Reward Properties That Score Well

- **Non-constant:** Score varies with agent quality (DQ check passes)
- **Non-binary:** Partial credit at every step (not just 0/1 at end)
- **Monotonic incentive:** Better submissions → higher reward (no reward hacking possible)
- **Difficulty-correlated:** Easy task baseline > medium > hard under same agent (evaluator check)
- **Penalizes degenerate behavior:** Loops, stagnation, regression explicitly penalized (PS.md compliance)

---

## 6. File-by-File Implementation Guide

### Project Structure

```
hackathon/data_cleaning_env/
├── __init__.py                          # Package exports
├── models.py                            # DataCleanAction, DataCleanObservation, DataCleanState
├── client.py                            # DataCleanEnv(EnvClient)
├── openenv.yaml                         # Environment manifest
├── pyproject.toml                       # Package metadata + dependencies
├── server/
│   ├── __init__.py                      # Server package exports
│   ├── app.py                           # create_app() wiring + main()
│   ├── data_cleaning_environment.py     # DataCleanEnvironment(Environment)
│   ├── graders.py                       # Grading logic + field comparison
│   ├── tasks/
│   │   ├── __init__.py                  # TASK_REGISTRY dict
│   │   ├── base.py                      # BaseTask ABC
│   │   ├── easy.py                      # Task 1: basic cleaning
│   │   ├── medium.py                    # Task 2: business rule transformation
│   │   ├── hard.py                      # Task 3: multi-source reconciliation
│   │   └── data/
│   │       ├── easy_input.json          # 50 rows, messy
│   │       ├── easy_expected.json       # 50 rows, clean (gold standard)
│   │       ├── medium_input.json        # 100 rows, raw transactions
│   │       ├── medium_rules.json        # Business rules spec
│   │       ├── medium_reference.json    # Tax rates, currency rates
│   │       ├── medium_expected.json     # Gold standard
│   │       ├── hard_source_a.json       # Source system A (~50 records)
│   │       ├── hard_source_b.json       # Source system B (~45 records)
│   │       ├── hard_source_c.json       # Source system C (~40 records)
│   │       ├── hard_spec.json           # Reconciliation rules
│   │       └── hard_expected.json       # Gold standard (~30 golden records)
│   └── Dockerfile                       # Multi-stage build
├── inference.py                         # Baseline agent (OpenAI client) — MUST be at root
└── README.md                            # Full documentation
```

### openenv.yaml

```yaml
spec_version: 1
name: data_cleaning_env
type: space
runtime: fastapi
app: server.app:app
port: 8000
```

### pyproject.toml

```toml
[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "openenv-data-cleaning-env"
version = "0.1.0"
description = "Data Cleaning & Transformation environment for OpenEnv"
requires-python = ">=3.11"
dependencies = [
    "openenv-core[core]>=0.2.2",
]

[project.optional-dependencies]
dev = ["pytest", "pytest-cov"]

[project.scripts]
server = "data_cleaning_env.server.app:main"

[tool.setuptools]
packages = ["data_cleaning_env", "data_cleaning_env.server", "data_cleaning_env.server.tasks"]

[tool.setuptools.package-dir]
data_cleaning_env = "."
```

### Dockerfile

Based on: `ref-repos/OpenEnv/src/openenv/cli/templates/openenv_env/server/Dockerfile`

```dockerfile
ARG BASE_IMAGE=ghcr.io/meta-pytorch/openenv-base:latest
FROM ${BASE_IMAGE} AS builder

WORKDIR /app
ARG BUILD_MODE=in-repo

COPY . /app/env
WORKDIR /app/env

RUN if ! command -v uv >/dev/null 2>&1; then \
        curl -LsSf https://astral.sh/uv/install.sh | sh && \
        mv /root/.local/bin/uv /usr/local/bin/uv; \
    fi

RUN apt-get update && apt-get install -y --no-install-recommends git

RUN --mount=type=cache,target=/root/.cache/uv \
    if [ -f uv.lock ]; then \
        uv sync --frozen --no-install-project --no-editable; \
    else \
        uv sync --no-install-project --no-editable; \
    fi

RUN --mount=type=cache,target=/root/.cache/uv \
    if [ -f uv.lock ]; then \
        uv sync --frozen --no-editable; \
    else \
        uv sync --no-editable; \
    fi

FROM ${BASE_IMAGE}
COPY --from=builder /app/env/.venv /app/.venv
COPY --from=builder /app/env /app/env

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/env:$PYTHONPATH"

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["sh", "-c", "cd /app/env && uvicorn server.app:app --host 0.0.0.0 --port 8000"]
```

### __init__.py (package root)

```python
"""Data Cleaning & Transformation environment for OpenEnv."""

from .client import DataCleanEnv
from .models import DataCleanAction, DataCleanObservation, DataCleanState

__all__ = ["DataCleanEnv", "DataCleanAction", "DataCleanObservation", "DataCleanState"]
```

### server/__init__.py

```python
"""Server package for Data Cleaning Environment."""

from .data_cleaning_environment import DataCleanEnvironment

__all__ = ["DataCleanEnvironment"]
```

### Task Base Class (`server/tasks/base.py`)

```python
"""Base class for all data cleaning tasks."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class GradeResult:
    score: float
    correct_fields: int
    total_fields: int
    errors: List[str] = field(default_factory=list)


class BaseTask(ABC):
    """Abstract base for a data cleaning task."""

    task_id: str
    description: str
    max_steps: int
    input_data: List[Dict[str, Any]]
    target_schema: Dict[str, Any]
    total_gradable_fields: int

    @abstractmethod
    def grade(self, submitted: List[Dict[str, Any]]) -> GradeResult:
        """Grade agent's submission. Returns GradeResult with score in [0.0, 1.0]."""
        ...
```

### Task Registry (`server/tasks/__init__.py`)

```python
"""Task registry for the data cleaning environment."""

from .easy import EasyTask
from .medium import MediumTask
from .hard import HardTask

TASK_REGISTRY = {
    "easy": EasyTask(),
    "medium": MediumTask(),
    "hard": HardTask(),
}
```

---

## 7. Inference Script — Exact Pattern

Based on: `ref-repos/OpenEnv/examples/coding_env_inference.py`, `ref-repos/OpenEnv/examples/finqa_inference.py`

The file MUST be named `inference.py` and placed at the **root** of the project.

```python
"""
Inference Script — Data Cleaning Environment
=============================================
MANDATORY:
- API_BASE_URL   The API endpoint for the LLM.
- MODEL_NAME     The model identifier to use for inference.
- HF_TOKEN       Your Hugging Face / API key.

The inference script must be named `inference.py` and placed in the root directory.
Participants must use OpenAI Client for all LLM calls.
"""

import json
import os
import sys
import textwrap
from typing import Any, Dict, List

from openai import OpenAI

# --- Environment imports ---
from data_cleaning_env import DataCleanAction, DataCleanEnv

# --- Credentials: support ALL key variants from PS.md (fail-fast) ---
API_BASE_URL = os.getenv("API_BASE_URL") or "https://router.huggingface.co/v1"
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY") or os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")

if not API_KEY:
    sys.exit("ERROR: No API key found. Set HF_TOKEN, API_KEY, or OPENAI_API_KEY.")
if not MODEL_NAME:
    sys.exit("ERROR: MODEL_NAME is not set.")

# --- Environment connection: dual-mode (URL-first, Docker fallback) ---
# PS.md does not guarantee evaluator starts the container before running this script.
# The sample inference (PS.md:316) uses from_docker_image, so we must support both:
#   Mode 1 (preferred): Connect to already-running server via ENV_URL
#   Mode 2 (fallback):  Spin up Docker container if no server is reachable
ENV_URL = os.getenv("ENV_URL", "http://localhost:8000")
DOCKER_IMAGE = os.getenv("DOCKER_IMAGE", "data-cleaning-env:latest")

# --- Agent config ---
MAX_TOKENS = 4096
TEMPERATURE = 0.2
TASKS = ["easy", "medium", "hard"]
# Per-task step limits matching environment max_steps (10/15/20)
TASK_MAX_STEPS = {"easy": 10, "medium": 15, "hard": 20}

SYSTEM_PROMPT = textwrap.dedent("""
    You are a data cleaning agent. You receive messy tabular data and a task description.
    Your job is to clean, transform, and fix the data according to the specification.

    Respond with ONLY a JSON array of cleaned records. No explanation, no markdown fences.
    Each record should be a JSON object matching the target schema.

    Rules:
    - Fix data types (dates to ISO 8601, numbers without currency symbols)
    - Remove exact duplicates
    - Standardize formatting (consistent case, trimmed whitespace)
    - Apply any business rules described in the task
    - Handle missing values appropriately
    - Process ALL records, not just the ones shown in examples
""").strip()


def build_user_prompt(observation, step: int, max_steps: int) -> str:
    """Build the prompt from the current observation. Sends ALL records."""
    records = observation.input_data
    record_count = len(records)

    prompt_parts = [
        f"## Task\n{observation.task_description}",
        f"\n## Target Schema\n```json\n{json.dumps(observation.target_schema, indent=2)}\n```",
    ]

    # Send ALL records — chunked into pages if too large for context
    # Serialize full dataset; let the model see everything
    data_json = json.dumps(records, indent=2)
    if len(data_json) > 80_000:
        # For very large datasets, send compact format
        data_json = json.dumps(records, separators=(",", ":"))
    prompt_parts.append(
        f"\n## Input Data ({record_count} records — ALL shown, process every one)\n"
        f"```json\n{data_json}\n```"
    )

    if observation.validation_errors:
        errors_to_show = observation.validation_errors[:30]
        prompt_parts.append(
            f"\n## Validation Errors from Previous Attempt ({len(observation.validation_errors)} total)\n"
            + "\n".join(f"- {e}" for e in errors_to_show)
        )
        prompt_parts.append(f"\nCurrent score: {observation.current_score:.3f}")
        prompt_parts.append(f"Step {step}/{max_steps} — fix the errors above to improve your score.")

    prompt_parts.append("\nRespond with ONLY the complete JSON array of all cleaned records.")
    return "\n".join(prompt_parts)


def parse_response(text: str) -> List[Dict[str, Any]]:
    """Extract JSON array from model response."""
    text = text.strip()
    # Strip markdown fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        pass
    return []


def run_task(env, client: OpenAI, task_id: str) -> Dict[str, Any]:
    """Run a single task and return results."""
    result = env.reset(task_id=task_id)
    observation = result.observation
    max_steps = TASK_MAX_STEPS.get(task_id, 10)

    print(f"\n{'='*60}")
    print(f"Task: {task_id} (max {max_steps} steps)")
    print(f"Description: {observation.task_description[:100]}...")
    print(f"Input records: {len(observation.input_data)}")

    best_score = 0.0
    for step in range(1, max_steps + 1):
        if result.done:
            break

        user_prompt = build_user_prompt(observation, step, max_steps)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        try:
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
            )
            response_text = completion.choices[0].message.content or ""
        except Exception as exc:
            print(f"  Step {step}: API error ({exc}), skipping")
            continue

        cleaned_data = parse_response(response_text)
        if not cleaned_data:
            print(f"  Step {step}: Failed to parse response, skipping")
            continue

        action = DataCleanAction(data=cleaned_data)
        result = env.step(action)
        observation = result.observation
        score = observation.current_score
        best_score = max(best_score, score)

        print(f"  Step {step}/{max_steps}: score={score:.3f} | errors={len(observation.validation_errors)} | reward={result.reward:.3f}")

        # Early exit if score is near-perfect
        if score >= 0.99:
            print(f"  Near-perfect score achieved, stopping early.")
            break

        if result.done:
            break

    print(f"  Final best score: {best_score:.3f}")
    return {"task_id": task_id, "best_score": best_score}


def _server_is_reachable(url: str, timeout: float = 3.0) -> bool:
    """Check if an OpenEnv server is already running at the given URL."""
    import urllib.request
    try:
        urllib.request.urlopen(f"{url}/health", timeout=timeout)
        return True
    except Exception:
        return False


def _connect_env():
    """Dual-mode connection: URL-first, Docker fallback.

    PS.md sample uses from_docker_image (line 316), but the evaluator may
    also start the container externally. We try both to be safe.
    """
    if _server_is_reachable(ENV_URL):
        print(f"Connecting to running server at {ENV_URL}")
        return DataCleanEnv(base_url=ENV_URL).sync()

    print(f"No server at {ENV_URL}, launching Docker image: {DOCKER_IMAGE}")
    import asyncio
    env = asyncio.run(DataCleanEnv.from_docker_image(DOCKER_IMAGE))
    return env.sync()


def main():
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    env = _connect_env()

    try:
        results = []
        for task_id in TASKS:
            task_result = run_task(env, client, task_id)
            results.append(task_result)

        print(f"\n{'='*60}")
        print("BASELINE RESULTS")
        print(f"{'='*60}")
        total = 0.0
        for r in results:
            print(f"  {r['task_id']:>8}: {r['best_score']:.3f}")
            total += r["best_score"]
        print(f"  {'average':>8}: {total / len(results):.3f}")
    finally:
        env.close()


if __name__ == "__main__":
    main()
```

---

## 8. Phased Execution with Validation Gates

### Phase 0 — Domain Lock & Task Spec (0.5 day)
**Where:** Claude Code

**Outputs:**
- Domain confirmed: Data Cleaning & Transformation
- Three task specs finalized with exact grading formulas
- Episode boundaries and max step limits set
- Test data design (column types, error types, record counts)

**Validation gate:**
- Each task has a written grading formula producing values in [0.0, 1.0]
- Easy/medium/hard difficulty is justified
- No grader can return constant scores (verify with mental walkthrough: perfect input → 1.0, empty input → 0.0, partial input → 0.0 < x < 1.0)

---

### Phase 1 — Scaffold & Skeleton (0.5 day)
**Where:** Claude Code

**Outputs:**
- Full directory structure created
- `models.py` with all Pydantic types
- `server/app.py` with canonical `create_app()` wiring
- `client.py` with EnvClient implementation
- `openenv.yaml` and `pyproject.toml`
- `server/Dockerfile`
- `__init__.py` files for all packages

**Validation gate:**
- All imports resolve (no circular dependencies)
- `pyproject.toml` has `[project.scripts] server = "..."` entry
- `server/app.py` has `def main(` and `if __name__` block
- `openenv.yaml` has all required fields

---

### Phase 2 — Environment Core Logic (1–1.5 days)
**Where:** Claude Code

**Outputs:**
- `server/data_cleaning_environment.py` with full `reset()`, `step()`, `state` implementation
- `server/tasks/base.py` with BaseTask ABC
- `server/tasks/easy.py`, `medium.py`, `hard.py` — task implementations
- `server/tasks/data/` — all JSON test data files
- `server/graders.py` — grading logic with field comparison

**Validation gate:**
- `reset()` returns clean state (no leakage from previous episode)
- `step()` returns valid observation with reward in [0.0, 1.0]
- Multiple resets with same seed produce identical initial observations
- Score distribution check: perfect submission → ~1.0, empty submission → ~0.0, partial → intermediate
- Easy task scores higher than hard under identical naive agent

---

### Phase 3 — Graders & Reward Verification (0.5–1 day)
**Where:** Claude Code

**Outputs:**
- All three graders produce scores in [0.0, 1.0] for all inputs
- Reward shaping provides per-step signal
- Edge cases handled (empty submission, wrong schema, extra fields, missing records)

**Validation gate (critical — DQ prevention):**
- Run 10 different submission qualities through each grader → verify non-constant output
- Run perfect submission → score >= 0.95
- Run empty submission → score == 0.0
- Run 50% correct submission → score approximately 0.5
- Run same submission twice → identical score (deterministic)

---

### Phase 4 — Inference Script (0.5–1 day)
**Where:** Claude Code (writing) + External (running)

**Outputs:**
- Root `inference.py` using OpenAI client
- Reads from `API_BASE_URL`, `MODEL_NAME`, and API key (`HF_TOKEN` / `API_KEY` / `OPENAI_API_KEY` fallback)
- Runs all 3 tasks
- Prints reproducible score summary

**Validation gate:**
- Script uses `from openai import OpenAI` (mandatory)
- No hardcoded API keys or model names
- Completes within 20 minutes on 2 vCPU / 8GB
- Produces scores for all 3 tasks without error

---

### Phase 5 — Docker & Local Runtime Validation (0.5–1 day)
**Where:** External (your terminal)

**Commands:**

```bash
# Generate lock file
cd hackathon/data_cleaning_env
uv lock

# Build Docker image
docker build -t data-cleaning-env:latest -f server/Dockerfile .

# Run container
docker run -p 8000:8000 data-cleaning-env:latest

# In another terminal — test endpoints manually
curl http://localhost:8000/health
curl http://localhost:8000/metadata
curl http://localhost:8000/schema

# Run OpenEnv runtime validation
openenv validate --url http://localhost:8000
```

**Validation gate (maps to exact validator checks from `_validation.py`):**

| Check | Endpoint | Expected |
|-------|----------|----------|
| OpenAPI version | `GET /openapi.json` | Returns `info.version` |
| Health | `GET /health` | Returns `{"status": "healthy"}` |
| Metadata | `GET /metadata` | Returns `name` and `description` |
| Schema | `GET /schema` | Returns action, observation, state JSON schemas |
| MCP | `POST /mcp` | Returns JSON-RPC payload |
| Mode consistency | OpenAPI endpoints | Matches OpenEnv simulation mode contract |

---

### Phase 6 — Documentation & HF Deployment (0.5–1 day)
**Where:** Claude Code (README) + External (deployment)

**README sections (all required by PS.md):**
1. Environment description and motivation
2. Action and observation space definitions
3. Task descriptions with expected difficulty
4. Setup and usage instructions
5. Baseline scores

**Deployment commands:**

```bash
# Login to Hugging Face
hf auth login

# Push to HF Spaces
openenv push --repo-id <username>/data-cleaning-env

# Validate deployed space
openenv validate https://<username>-data-cleaning-env.hf.space
```

**Validation gate:**
- Space URL returns 200
- `reset()` responds correctly from deployed Space
- README renders properly on HF

---

### Phase 7 — Final Validation & Polish (0.5 day)
**Where:** Claude Code + External

**Full pre-submission run:**

```bash
# 1) Local structure validation
openenv validate --verbose

# 2) Docker build and run
docker build -t data-cleaning-env:latest -f server/Dockerfile .
docker run -p 8000:8000 data-cleaning-env:latest

# 3) Runtime validation
openenv validate --url http://localhost:8000

# 4) Baseline inference
export API_BASE_URL="https://router.huggingface.co/v1"
export MODEL_NAME="openai/gpt-oss-120b:novita"
export HF_TOKEN="hf_xxx"
python inference.py

# 5) Deploy to HF
openenv push --repo-id <username>/data-cleaning-env

# 6) Validate deployed space
openenv validate https://<username>-data-cleaning-env.hf.space
```

---

## 9. Validator Compliance — Hard Requirements

From: `ref-repos/OpenEnv/src/openenv/cli/_validation.py`

### Local Validation Checks

| # | Check | How We Pass |
|---|-------|-------------|
| 1 | `pyproject.toml` exists | Created in Phase 1 |
| 2 | `uv.lock` exists | Run `uv lock` in Phase 5 |
| 3 | `[project.scripts]` has `server` entry | `server = "data_cleaning_env.server.app:main"` |
| 4 | Server entry contains `:main` | `app:main` format ✓ |
| 5 | `openenv-core` in dependencies | `openenv-core[core]>=0.2.2` ✓ |
| 6 | `server/app.py` exists | Created in Phase 1 |
| 7 | `server/app.py` has `def main(` | Included in template ✓ |
| 8 | `server/app.py` has `if __name__` | Included in template ✓ |

### Runtime Validation Checks

| # | Check | How We Pass |
|---|-------|-------------|
| 1 | `GET /openapi.json` returns version | Provided by `create_app()` automatically |
| 2 | `GET /health` returns healthy | Provided by `create_app()` automatically |
| 3 | `GET /metadata` returns name + description | `get_metadata()` implemented in environment |
| 4 | `GET /schema` returns action/obs/state schemas | Provided by `create_app()` from Pydantic models |
| 5 | `POST /mcp` returns JSON-RPC | Provided by `create_app()` automatically |
| 6 | Endpoint-mode consistency | Using standard `create_app()` ensures this |

---

## 10. Failure Modes & Mitigations

| # | Failure Mode | Risk Level | Mitigation |
|---|-------------|------------|------------|
| 1 | **Constant grader outputs** | DQ | Test score spread: perfect=1.0, empty=0.0, partial=0.3-0.7 before shipping |
| 2 | **State leakage across resets** | Non-reproducible scores | Fully reinitialize `_state`, `_task`, `_best_score`, `_previous_score`, `_last_action_hash`, `_no_progress_streak` in `reset()` |
| 3 | **Sparse terminal-only reward** | Weak agentic evaluation | Composite reward with absolute + improvement + loop/stagnation penalties every step |
| 4 | **Hardcoded model settings** | Evaluator infra fail | Support all key variants: `HF_TOKEN`, `API_KEY`, `OPENAI_API_KEY`. Fail-fast with clear error. |
| 5 | **Docker builds but runtime fails** | Phase 1 automation fail | Run `openenv validate --url` on local container before push |
| 6 | **Base image unavailable** | Build fails | Fallback: replace `FROM ghcr.io/meta-pytorch/openenv-base:latest` with `FROM python:3.11-slim` + manual pip install |
| 7 | **Inference timeout (>20 min)** | DQ | Per-task step limits (10/15/20) × 3 tasks = max 45 LLM calls. Bounded data sizes (50/100/60 records). Early exit on score >= 0.99. |
| 8 | **Memory exceeded (>8GB)** | Runtime fail | JSON data files total <1MB. No pandas/heavy libs. Pure dict operations |
| 9 | **`openenv-core` API drift from course examples** | Import errors | All patterns verified against actual `ref-repos/OpenEnv/src/` source, not course text |
| 10 | **Reward gaming** | Human review flag | Gold standard hidden server-side. Agent only sees validation errors, not expected values |
| 11 | **Inference connection mode unknown** | Baseline fails if evaluator expects Docker self-launch or pre-started server | Dual-mode: probe `ENV_URL` first, fall back to `from_docker_image(DOCKER_IMAGE)`. Both configurable via env vars. |
| 12 | **Prompt truncation suppresses baseline quality** | Lower Phase 2 scores | Send ALL records in prompt. Use compact JSON if data exceeds 80K chars. |
| 13 | **No loop penalty despite PS.md requirement** | Human review flags incomplete reward | Explicit repeat-action penalty (-0.15) and stagnation penalty (-0.1 × streak). |
| 14 | **inference.py not at project root** | DQ | Submission repo is dedicated env repo. `inference.py` is at its root. Not the monorepo. |

---

## 11. External Dependencies & Environment Setup

### Required Software

| Tool | Version | Purpose |
|------|---------|---------|
| Python | >= 3.11 | Runtime |
| `uv` | Latest | Dependency management + lock file |
| Docker | Latest | Container build + test |
| `openenv-core` | >= 0.2.2 | Framework + validation CLI |
| `openai` (Python SDK) | Latest | Inference script (mandatory per PS.md) |

### Required Environment Variables

```bash
export API_BASE_URL="https://router.huggingface.co/v1"
export MODEL_NAME="openai/gpt-oss-120b:novita"
export HF_TOKEN="hf_your_token_here"
```

### What Happens in Claude Code vs External

| Work | Claude Code | External |
|------|:-----------:|:--------:|
| All code writing | Yes | — |
| All config files | Yes | — |
| Test data generation | Yes | — |
| README | Yes | — |
| `uv lock` | — | Yes |
| Docker build + run | — | Yes |
| Local endpoint testing | — | Yes |
| `openenv validate` (local + runtime) | — | Yes |
| Running `inference.py` | — | Yes |
| HF Spaces deployment | — | Yes |

**~80% in Claude Code, ~20% external.**

---

## 12. Pre-Submission Checklist

### DQ Prevention (All must pass)

- [ ] HF Space deploys and returns 200 on ping
- [ ] Space responds to `reset()` correctly
- [ ] `openenv validate` passes (local + runtime)
- [ ] `docker build && docker run` works cleanly
- [ ] `inference.py` completes without error
- [ ] `inference.py` produces scores for all 3 tasks
- [ ] All grader scores are in [0.0, 1.0] range
- [ ] Graders are non-constant (different inputs → different scores)
- [ ] No plagiarized or trivially modified existing environments

### Scoring Maximizers

- [ ] Reward provides per-step partial signal (not terminal-only)
- [ ] Easy task baseline > medium > hard (difficulty progression confirmed)
- [ ] Hard task genuinely challenges frontier models (score < 0.3 for baseline)
- [ ] README contains all 5 required sections
- [ ] Action/observation types are well-documented with Field descriptions
- [ ] Domain is novel (not email triage, not a game, not a toy)
- [ ] Environment resets cleanly (no state leakage across episodes)

### Final Deployment Sequence

```bash
# 1) Generate lock file
cd hackathon/data_cleaning_env && uv lock

# 2) Local structure validation
openenv validate --verbose

# 3) Docker build
docker build -t data-cleaning-env:latest -f server/Dockerfile .

# 4) Docker run + runtime validation
docker run -p 8000:8000 data-cleaning-env:latest
# (in another terminal)
openenv validate --url http://localhost:8000

# 5) Run baseline inference
export API_BASE_URL="https://router.huggingface.co/v1"
export MODEL_NAME="openai/gpt-oss-120b:novita"
export HF_TOKEN="hf_xxx"
python inference.py

# 6) Record baseline scores in README

# 7) Deploy to HF Spaces
openenv push --repo-id <username>/data-cleaning-env

# 8) Validate deployed space
openenv validate https://<username>-data-cleaning-env.hf.space

# 9) Final smoke test: hit the deployed Space URL directly (not Docker)
#    This verifies the live HF Space, not a local registry image.
python -c "
from data_cleaning_env import DataCleanEnv
env = DataCleanEnv(base_url='https://<username>-data-cleaning-env.hf.space').sync()
result = env.reset(task_id='easy')
obs = result.observation
print(f'Task: {obs.task_description[:50]}...')
print(f'Records: {len(obs.input_data)}')
env.close()
"
```

---

## 13. Submission Structure — Repo Layout

### Critical Rule

PS.md lines 407-412 ask for a **GitHub repo URL** and an **HF Space URL**. The submitted GitHub repo IS the project root. `inference.py` must be at that root.

**Our submission is a dedicated repo, NOT the hackathon monorepo.**

The submitted repo looks exactly like:

```
my-data-cleaning-env/        ← This IS the GitHub repo root
├── __init__.py
├── models.py
├── client.py
├── openenv.yaml
├── pyproject.toml
├── inference.py              ← MUST be here (root of submitted repo)
├── README.md
└── server/
    ├── __init__.py
    ├── app.py
    ├── data_cleaning_environment.py
    ├── graders.py
    ├── tasks/
    │   ├── __init__.py
    │   ├── base.py
    │   ├── easy.py
    │   ├── medium.py
    │   ├── hard.py
    │   └── data/
    │       └── *.json
    └── Dockerfile
```

### Workflow

1. Build everything in `hackathon/data_cleaning_env/` within this monorepo
2. When ready to submit, push that directory's contents to a **dedicated GitHub repo**
3. Submit that repo URL + the HF Space URL

---

## 14. Resolved Ambiguities from PS.md

Issues identified by Codex-5.3-max review, resolved here:

### Credentials Contract (HIGH)

**Problem:** PS.md line 45 says `OPENAI_API_KEY`, but checklist (lines 199-206) and sample (lines 249-251) use `API_BASE_URL` + `MODEL_NAME` + `HF_TOKEN`/`API_KEY`.

**Resolution:** The sample code is authoritative. Support all variants in fallback order:
```python
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY") or os.getenv("OPENAI_API_KEY")
```
Fail-fast with clear error if none are set.

### Double-Slash Bug in Sample (INFO)

**Problem:** PS.md line 175 has `os.getenv("API_BASE_URL") // "https://..."` — Python floor division, not null coalescing.

**Resolution:** This is a typo in the PS. Use `or` instead. Do NOT copy literally.

### inference.py Location (HIGH)

**Problem:** PS.md says "root directory of the project" — ambiguous if submitting a monorepo.

**Resolution:** Submit a **dedicated repo**. `inference.py` goes at that repo's root. Not the monorepo root.

### Inference Docker Dependency (HIGH)

**Problem:** Original plan used `from_docker_image("data-cleaning-env:latest")` — fails if evaluator doesn't have that tag. But PS.md sample (line 316) itself uses `from_docker_image`, so evaluator may expect the script to self-launch.

**Resolution:** Dual-mode connection. Try URL first (server already running), fall back to Docker.
See `_connect_env()` in Section 7 for the full async-correct implementation. Simplified logic:
```python
# 1. Probe running server
if _server_is_reachable(ENV_URL):
    env = DataCleanEnv(base_url=ENV_URL).sync()
# 2. Fall back to Docker (async — must be awaited)
else:
    env = asyncio.run(DataCleanEnv.from_docker_image(DOCKER_IMAGE)).sync()
```
Both `ENV_URL` and `DOCKER_IMAGE` are configurable via env vars.

### Fixed Step Loop vs Per-Task Limits (MEDIUM)

**Problem:** Original plan used `range(1, 11)` for all tasks, but tasks define 10/15/20 max steps.

**Resolution:** Read per-task limits:
```python
TASK_MAX_STEPS = {"easy": 10, "medium": 15, "hard": 20}
```

### Prompt Truncation (MEDIUM)

**Problem:** Original plan sent only first 20 records but asked agent to process all.

**Resolution:** Send ALL records. Use compact JSON (`separators=(",",":")`) if payload exceeds 80K chars.

### Missing Loop Penalty (MEDIUM)

**Problem:** PS.md line 41 requires penalizing "infinite loops, destructive actions" but original reward formula had no loop detection.

**Resolution:** Added:
- `repeat_penalty = 0.15` if exact same action submitted twice consecutively
- `stagnation_penalty = 0.1 × consecutive_no_progress_steps` (capped at 0.3)
- `regression_penalty = 0.05 × score_decrease` for destructive changes

---

## 15. Research Sources

### Hackathon Requirements
- `hackathon/docs/PS.md`

### Course Modules
- `README.md` — Course overview
- `module-1/README.md` — OpenEnv architecture, 3-method interface
- `module-2/README.md` — Using existing environments, policy patterns
- `module-3/README.md` — Deployment (Uvicorn, Docker, HF Spaces)
- `module-4/README.md` — Building environments (3-component pattern)
- `module-5/README.md` — GRPO training with TRL

### OpenEnv Framework Source
- `ref-repos/OpenEnv/src/openenv/core/env_server/types.py` — Action, Observation, State base classes
- `ref-repos/OpenEnv/src/openenv/core/env_server/interfaces.py` — Environment ABC
- `ref-repos/OpenEnv/src/openenv/core/env_server/http_server.py` — `create_app()` signature (line 1489)
- `ref-repos/OpenEnv/src/openenv/core/env_client.py` — EnvClient base class
- `ref-repos/OpenEnv/src/openenv/core/client_types.py` — StepResult type

### Validation
- `ref-repos/OpenEnv/src/openenv/cli/_validation.py` — Local + runtime validation checks
- `ref-repos/OpenEnv/src/openenv/cli/_cli_utils.py` — CLI utilities
- `ref-repos/OpenEnv/src/openenv/cli/commands/validate.py` — Validate command

### Existing Environment Implementations
- `ref-repos/OpenEnv/envs/echo_env/` — Minimal reference (MCP-based)
- `ref-repos/OpenEnv/envs/coding_env/` — Complex reference (code execution)
- `ref-repos/OpenEnv/envs/finqa_env/server/rewards.py` — Real-world reward: numeric tolerance with dual checks
- `ref-repos/OpenEnv/envs/repl_env/rubrics.py` — Rubric patterns: ExactMatch, CustomMetric, Composite

### CLI Templates
- `ref-repos/OpenEnv/src/openenv/cli/templates/openenv_env/` — Canonical scaffold (all files)

### Inference Examples
- `ref-repos/OpenEnv/examples/finqa_inference.py` — MCP tool-calling inference
- `ref-repos/OpenEnv/examples/coding_env_inference.py` — Iterative feedback-loop inference
- `ref-repos/OpenEnv/examples/textarena_wordle_inference.py` — Game-style inference

### Design Documents
- `ref-repos/OpenEnv/rfcs/004-rubrics.md` — Rubric system design
- `ref-repos/OpenEnv/rfcs/002-env-spec.md` — Environment specification
- `ref-repos/OpenEnv/rfcs/001-abstractions.md` — Design philosophy
- `ref-repos/OpenEnv/docs/environment-builder.md` — Official builder guide
- `ref-repos/OpenEnv/docs/contributing-envs.md` — Contributing environments guide
- `ref-repos/OpenEnv/docs/quickstart.md` — Quick start
- `ref-repos/OpenEnv/docs/cli.md` — CLI reference
