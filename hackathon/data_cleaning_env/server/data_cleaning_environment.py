"""Runtime environment implementation for data cleaning episodes."""

from __future__ import annotations

import json
from hashlib import sha1
from typing import Any, Dict, List, Optional
from uuid import uuid4

try:
    from openenv.core.env_server.interfaces import Environment
except Exception:
    class Environment:
        """Fallback environment base when openenv-core is unavailable."""


try:
    from ..models import DataCleanAction, DataCleanObservation, DataCleanState
    from .graders import grade_submission
    from .tasks import TASK_REGISTRY
except (ModuleNotFoundError, ImportError):
    from models import DataCleanAction, DataCleanObservation, DataCleanState
    from server.graders import grade_submission
    from server.tasks import TASK_REGISTRY


class DataCleanEnvironment(Environment):
    """Environment with deterministic reset/step transitions and shaped rewards."""

    SUPPORTS_CONCURRENT_SESSIONS = True

    def __init__(self) -> None:
        self._state = DataCleanState(episode_id=str(uuid4()), step_count=0)
        self._task = None
        self._best_score = 0.0
        self._previous_score = 0.0
        self._last_action_fingerprint: Optional[str] = None
        self._no_progress_streak = 0

    def reset(
        self,
        seed: Optional[int] = None,
        episode_id: Optional[str] = None,
        **kwargs: Any,
    ) -> DataCleanObservation:
        del seed

        task_id = kwargs.get("task_id", "easy")
        if task_id not in TASK_REGISTRY:
            available = ", ".join(sorted(TASK_REGISTRY.keys()))
            raise ValueError(f"Unknown task_id '{task_id}'. Available task_ids: {available}")

        task = TASK_REGISTRY[task_id]
        self._task = task
        self._best_score = 0.0
        self._previous_score = 0.0
        self._last_action_fingerprint = None
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
            metadata={
                "task_id": task_id,
                "step": 0,
                "best_score": 0.0,
                "correct_fields": 0,
                "total_fields": task.total_gradable_fields,
                "no_progress_streak": 0,
                "repeat_action": False,
                "done_reason": "in_progress",
            },
        )

    def step(
        self,
        action: DataCleanAction,
        timeout_s: Optional[float] = None,
        **kwargs: Any,
    ) -> DataCleanObservation:
        del timeout_s

        if self._task is None:
            self.reset(task_id=kwargs.get("task_id", "easy"))

        self._state.step_count += 1
        step = self._state.step_count

        result = grade_submission(self._task, action.data)
        score = float(result.score)
        errors = list(result.errors)
        correct_fields = int(result.correct_fields)
        self._state.correct_fields = correct_fields

        fingerprint = self._fingerprint_action(action.data)
        is_repeat = fingerprint == self._last_action_fingerprint
        self._last_action_fingerprint = fingerprint

        if abs(score - self._previous_score) < 1e-3:
            self._no_progress_streak += 1
        else:
            self._no_progress_streak = 0

        improvement = max(0.0, score - self._previous_score)
        regression_term = max(0.0, self._previous_score - score)
        repeat_penalty = 0.15 if is_repeat else 0.0
        stagnation_penalty = min(0.1 * self._no_progress_streak, 0.3)

        raw_reward = (
            0.50 * score
            + 0.25 * improvement
            - 0.05 * regression_term
            - repeat_penalty
            - stagnation_penalty
        )
        reward = max(0.0, min(1.0, raw_reward))

        self._previous_score = score
        self._best_score = max(self._best_score, score)

        reached_target = score >= 0.99
        reached_limit = step >= self._state.max_steps
        done = reached_target or reached_limit
        if reached_target:
            done_reason = "target_score"
        elif reached_limit:
            done_reason = "max_steps"
        else:
            done_reason = "in_progress"

        return DataCleanObservation(
            task_description=self._task.description,
            input_data=self._task.input_data,
            target_schema=self._task.target_schema,
            validation_errors=errors,
            current_score=score,
            done=done,
            reward=reward,
            metadata={
                "task_id": self._state.task_id,
                "step": step,
                "best_score": self._best_score,
                "correct_fields": correct_fields,
                "total_fields": self._state.total_fields,
                "no_progress_streak": self._no_progress_streak,
                "repeat_action": is_repeat,
                "done_reason": done_reason,
            },
        )

    @property
    def state(self) -> DataCleanState:
        return self._state

    def get_metadata(self) -> Any:
        try:
            from openenv.core.env_server.types import EnvironmentMetadata

            return EnvironmentMetadata(
                name="data_cleaning_env",
                description="Data Cleaning & Transformation environment for AI agents",
                version="0.1.0",
            )
        except Exception:
            return {
                "name": "data_cleaning_env",
                "description": "Data Cleaning & Transformation environment for AI agents",
                "version": "0.1.0",
            }

    @staticmethod
    def _fingerprint_action(data: List[Dict[str, Any]]) -> str:
        try:
            canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        except (TypeError, ValueError):
            canonical = str(data)
        return sha1(canonical.encode("utf-8")).hexdigest()
