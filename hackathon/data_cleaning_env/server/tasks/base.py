"""Base task abstractions for Session 1 scaffold."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class GradeResult:
    """Minimal grading result structure for later sessions."""

    score: float
    correct_fields: int = 0
    total_fields: int = 0
    errors: List[str] = field(default_factory=list)


class BaseTask(ABC):
    """Abstract base class for all data cleaning tasks."""

    task_id: str
    description: str
    max_steps: int
    input_data: List[Dict[str, Any]]
    target_schema: Dict[str, Any]
    total_gradable_fields: int

    @abstractmethod
    def grade(self, submitted: List[Dict[str, Any]]) -> GradeResult:
        """Score a submitted record set with deterministic logic."""
        raise NotImplementedError
