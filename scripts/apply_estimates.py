#!/usr/bin/env python3
"""Fill missing budget hours using the Security Team Task Tracker estimates."""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def build_estimate_lookup(tracker_path: Path) -> pd.Series:
    raw = pd.read_excel(tracker_path, sheet_name="Project & Task Summary", header=1)
    df = raw[["Project ID", "Task Code", "Estimates"]].dropna()
    df["Project ID"] = df["Project ID"].astype(str).str.strip()
    df["Task Code"] = df["Task Code"].astype(str).str.strip().str.upper()
    grouped = df.groupby(["Project ID", "Task Code"])["Estimates"].sum()
    return grouped


def match_estimate(project_id: str, task_code: str, lookup: pd.Series) -> float | None:
    candidate = project_id
    while candidate:
        key = (candidate, task_code)
        if key in lookup.index:
            return lookup.loc[key]
        if "." in candidate:
            candidate = candidate.rsplit(".", 1)[0]
        else:
            break
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tracker",
        default="Security Team Task Tracker v2.xlsx",
        help="Path to the Security Team Task Tracker workbook (default: %(default)s)",
    )
    parser.add_argument(
        "--report",
        default="reports/timely-burndown.xlsx",
        help="Path to the Timely burndown workbook to update (default: %(default)s)",
    )
    args = parser.parse_args()

    tracker_path = Path(args.tracker)
    report_path = Path(args.report)

    if not tracker_path.exists():
        raise FileNotFoundError(f"Tracker file not found: {tracker_path}")
    if not report_path.exists():
        raise FileNotFoundError(f"Report file not found: {report_path}")

    lookup = build_estimate_lookup(tracker_path)
    tasks = pd.read_excel(report_path, sheet_name="Project Tasks")
    tasks["Project ID Key"] = tasks["Project"].astype(str).str.split(":", n=1).str[0].str.strip()
    tasks["Task Code"] = tasks["Task Code"].astype(str).str.strip().str.upper()

    filled = 0
    estimates = []
    for pid, code, current in zip(tasks["Project ID Key"], tasks["Task Code"], tasks["Budget Hours"]):
        if pd.notna(current):
            estimates.append(current)
            continue
        estimate = match_estimate(pid, code, lookup)
        if estimate is not None:
            estimates.append(estimate)
            filled += 1
        else:
            estimates.append(current)

    tasks["Budget Hours"] = estimates
    tasks["Hours Remaining"] = tasks["Budget Hours"] - tasks["Logged Hours"]
    tasks = tasks.drop(columns=["Project ID Key"])

    summary = pd.read_excel(report_path, sheet_name="Project Summary")
    summary = summary.drop(columns=[col for col in summary.columns if col not in {"Project", "Logged Hours", "Budget Hours", "Hours Remaining"}], errors="ignore")
    summary = (
        tasks.groupby("Project", dropna=False)[["Logged Hours", "Budget Hours"]]
        .sum(min_count=1)
        .reset_index()
    )
    summary["Hours Remaining"] = summary["Budget Hours"] - summary["Logged Hours"]

    with pd.ExcelWriter(report_path, engine="openpyxl", mode="w") as writer:
        tasks.to_excel(writer, sheet_name="Project Tasks", index=False)
        summary.to_excel(writer, sheet_name="Project Summary", index=False)

    print(f"Filled budget hours for {filled} rows using tracker estimates.")


if __name__ == "__main__":
    main()
