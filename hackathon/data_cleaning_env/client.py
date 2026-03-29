"""Client scaffold for the Data Cleaning OpenEnv environment."""

from dataclasses import dataclass
from typing import Any, Dict, Generic, Optional, TypeVar

from .models import DataCleanAction, DataCleanObservation, DataCleanState

A = TypeVar("A")
O = TypeVar("O")
S = TypeVar("S")

try:
    from openenv.core.client_types import StepResult
    from openenv.core.env_client import EnvClient
except Exception:
    @dataclass
    class StepResult(Generic[O]):
        """Fallback StepResult when openenv-core is unavailable."""

        observation: O
        reward: Optional[float] = None
        done: bool = False

    class EnvClient(Generic[A, O, S]):
        """Fallback EnvClient stub for Session 1 scaffold."""


class DataCleanEnv(EnvClient[DataCleanAction, DataCleanObservation, DataCleanState]):
    """Compile-safe client skeleton for Session 1."""

    def _step_payload(self, action: DataCleanAction) -> Dict[str, Any]:
        return {"data": action.data}

    def _parse_result(self, payload: Dict[str, Any]) -> StepResult[DataCleanObservation]:
        obs_payload = payload.get("observation", {}) or {}
        observation = DataCleanObservation(
            task_description=obs_payload.get("task_description", ""),
            input_data=obs_payload.get("input_data", []),
            target_schema=obs_payload.get("target_schema", {}),
            validation_errors=obs_payload.get("validation_errors", []),
            current_score=obs_payload.get("current_score", 0.0),
            done=payload.get("done", False),
            reward=payload.get("reward"),
            metadata=obs_payload.get("metadata", {}),
        )
        return StepResult(
            observation=observation,
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict[str, Any]) -> DataCleanState:
        return DataCleanState(
            episode_id=payload.get("episode_id", ""),
            step_count=payload.get("step_count", 0),
            task_id=payload.get("task_id", "easy"),
            total_fields=payload.get("total_fields", 0),
            correct_fields=payload.get("correct_fields", 0),
            max_steps=payload.get("max_steps", 10),
        )
