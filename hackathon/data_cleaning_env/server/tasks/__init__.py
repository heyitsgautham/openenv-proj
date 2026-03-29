"""Task registry scaffold for the Data Cleaning environment."""

from typing import Dict

from .base import BaseTask
from .easy import EasyTask
from .hard import HardTask
from .medium import MediumTask

TASK_REGISTRY: Dict[str, BaseTask] = {
	"easy": EasyTask(),
	"medium": MediumTask(),
	"hard": HardTask(),
}

__all__ = ["TASK_REGISTRY", "BaseTask"]
