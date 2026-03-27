"""Excel export helpers."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

from .models import TaskRollup


def export_rollups_to_excel(rollups: Iterable[TaskRollup], output_path: Path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = [
        {
            "Project ID": rollup.project_id,
            "Project": rollup.project_name,
            "Task Code": rollup.task_code,
            "Task Name": rollup.task_name,
            "Logged Hours": round(rollup.logged_hours, 2),
            "Budget Hours": None if rollup.budget_hours is None else round(rollup.budget_hours, 2),
            "Hours Remaining": None if rollup.remaining_hours is None else round(rollup.remaining_hours, 2),
        }
        for rollup in rollups
    ]

    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame(
            columns=[
                "Project ID",
                "Project",
                "Task Code",
                "Task Name",
                "Logged Hours",
                "Budget Hours",
                "Hours Remaining",
            ]
        )

    df.sort_values(["Project", "Task Code"], inplace=True, ignore_index=True)

    summary = (
        df.groupby("Project", dropna=False)[["Logged Hours", "Budget Hours"]]
        .sum(min_count=1)
        .reset_index()
    )
    summary["Hours Remaining"] = summary["Budget Hours"] - summary["Logged Hours"]

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Project Tasks", index=False)
        summary.to_excel(writer, sheet_name="Project Summary", index=False)

    return output_path
