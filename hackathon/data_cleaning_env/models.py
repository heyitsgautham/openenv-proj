"""Typed models scaffold for the Data Cleaning OpenEnv environment."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

try:
    from openenv.core.env_server.types import Action, Observation, State
except Exception:
    class Action(BaseModel):
        """Fallback action base when openenv-core is unavailable."""

    class Observation(BaseModel):
        """Fallback observation base when openenv-core is unavailable."""

        done: bool = False
        reward: Optional[float] = None
        metadata: Dict[str, Any] = Field(default_factory=dict)

    class State(BaseModel):
        """Fallback state base when openenv-core is unavailable."""

        episode_id: str = ""
        step_count: int = 0


class DataCleanAction(Action):
    """Agent action payload scaffold."""

    data: List[Dict[str, Any]] = Field(default_factory=list, description="Agent submitted records.")


class DataCleanObservation(Observation):
    """Observation payload scaffold."""

    task_description: str = Field(default="", description="Task prompt for the agent.")
    input_data: List[Dict[str, Any]] = Field(default_factory=list, description="Raw task input records.")
    target_schema: Dict[str, Any] = Field(default_factory=dict, description="Expected output schema.")
    validation_errors: List[str] = Field(default_factory=list, description="Validation hints from grader.")
    current_score: float = Field(default=0.0, description="Current score for latest submission.")


class DataCleanState(State):
    """Episode state scaffold."""

    task_id: str = Field(default="easy", description="Current task identifier.")
    total_fields: int = Field(default=0, ge=0, description="Total gradable fields.")
    correct_fields: int = Field(default=0, ge=0, description="Number of currently correct fields.")
    max_steps: int = Field(default=10, ge=1, description="Maximum steps for the active task.")
