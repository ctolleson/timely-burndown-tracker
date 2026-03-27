"""Core aggregation helpers."""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List, Mapping, MutableMapping, Optional, Tuple

from .models import TaskRollup

TaskKey = Tuple[int, str]


def derive_task_code(comment: Optional[str], prefix_len: int = 4) -> str:
    if not comment:
        return "UNKN"
    letters = [ch for ch in comment if ch.isalpha()]
    prefix = "".join(letters[:prefix_len]) or comment.strip()[:prefix_len]
    prefix = prefix or "UNKN"
    return prefix.upper()


def minutes_from_duration(duration: Optional[Mapping[str, float]]) -> float:
    if not duration:
        return 0.0
    if "total_minutes" in duration and duration["total_minutes"] is not None:
        return float(duration["total_minutes"])
    if "total_seconds" in duration and duration["total_seconds"] is not None:
        return float(duration["total_seconds"]) / 60
    hours = duration.get("hours", 0) or 0
    minutes = duration.get("minutes", 0) or 0
    seconds = duration.get("seconds", 0) or 0
    return float(hours) * 60 + float(minutes) + float(seconds) / 60


def aggregate_rollups(
    *,
    projects: Iterable[Mapping[str, object]],
    events: Iterable[Mapping[str, object]],
    forecasts: Iterable[Mapping[str, object]],
    prefix_len: int = 4,
) -> List[TaskRollup]:
    project_lookup: Dict[int, Mapping[str, object]] = {
        int(project["id"]): project for project in projects if project.get("id") is not None
    }

    usage_minutes: MutableMapping[TaskKey, float] = defaultdict(float)
    task_labels: Dict[TaskKey, str] = {}

    for event in events:
        project_id = _extract_project_id(event)
        if project_id is None:
            continue
        note = (event.get("note") or event.get("description") or "").strip()
        code = derive_task_code(note, prefix_len)
        if not code:
            continue
        duration = minutes_from_duration(event.get("duration"))
        usage_minutes[(project_id, code)] += duration
        if (project_id, code) not in task_labels and note:
            task_labels[(project_id, code)] = note

    budget_minutes: MutableMapping[TaskKey, float] = defaultdict(float)
    for forecast in forecasts:
        project_id = forecast.get("project_id")
        if project_id is None:
            continue
        title = (forecast.get("title") or forecast.get("note") or "").strip()
        code = derive_task_code(title, prefix_len)
        minutes = _forecast_minutes(forecast)
        if minutes <= 0:
            continue
        budget_minutes[(int(project_id), code)] += minutes
        task_labels.setdefault((int(project_id), code), title or code)

    rollups: List[TaskRollup] = []
    for key in sorted(set(usage_minutes) | set(budget_minutes)):
        project_id, code = key
        project_name = str(project_lookup.get(project_id, {}).get("name", "Unknown"))
        rollups.append(
            TaskRollup(
                project_id=project_id,
                project_name=project_name,
                task_code=code,
                task_name=task_labels.get(key, code),
                logged_minutes=usage_minutes.get(key, 0.0),
                budget_minutes=budget_minutes.get(key),
            )
        )
    return rollups


def _extract_project_id(event: Mapping[str, object]) -> Optional[int]:
    if "project_id" in event and event.get("project_id") is not None:
        return int(event["project_id"])
    project_obj = event.get("project")
    if isinstance(project_obj, Mapping) and project_obj.get("id") is not None:
        return int(project_obj["id"])
    return None


def _forecast_minutes(forecast: Mapping[str, object]) -> float:
    estimated = forecast.get("estimated_minutes")
    if estimated:
        return float(estimated)
    duration = forecast.get("estimated_duration")
    if isinstance(duration, Mapping):
        total = duration.get("total_minutes")
        if total:
            return float(total)
    return 0.0
