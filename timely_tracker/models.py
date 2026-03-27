"""Domain models for Timely burndown reports."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class TaskRollup:
    project_id: int
    project_name: str
    task_code: str
    task_name: str
    logged_minutes: float
    budget_minutes: Optional[float]

    @property
    def remaining_minutes(self) -> Optional[float]:
        if self.budget_minutes is None:
            return None
        return self.budget_minutes - self.logged_minutes

    @property
    def logged_hours(self) -> float:
        return self.logged_minutes / 60

    @property
    def budget_hours(self) -> Optional[float]:
        return None if self.budget_minutes is None else self.budget_minutes / 60

    @property
    def remaining_hours(self) -> Optional[float]:
        remaining = self.remaining_minutes
        return None if remaining is None else remaining / 60
