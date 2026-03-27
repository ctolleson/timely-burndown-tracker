# Timely Burndown Tracker

This project fetches projects, logged events, and task forecasts from [Timely](https://app.timelyapp.com) and produces an Excel workbook that tracks how much time has been spent vs. planned for every project/task combination. Tasks are inferred from the first four letters of each Timely comment, so consistent prefixes (e.g., `BILL-`, `FEAT`, `ADMN`) map usage back to the correct task bucket.

## Features

- Pulls projects via `GET /1.1/:account_id/projects`, logged hours via `GET /1.1/:account_id/events`, and optional task forecasts via `GET /1.1/:account_id/forecasts`.
- Derives task codes from the first four alphabetic characters of an event/forecast comment.
- Aggregates logged vs. budgeted minutes per project/task and writes an Excel workbook with two sheets:
  - `Project Tasks`: each project-task row with logged hours, budget hours, and hours remaining.
  - `Project Summary`: project-level totals for quick burndown checks.
- Simple Typer-based CLI (`timely-tracker export`) with options for date ranges, output path, and task prefix length.

## Getting Started

1. **Python environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e .
   ```

2. **Environment variables** – copy `.env.example` and fill in your Timely account settings.
   ```bash
   cp .env.example .env
   ````

   | Variable | Purpose |
   | --- | --- |
   | `TIMELY_ACCOUNT_ID` | Numeric Timely account identifier (visible in the browser URL). |
   | `TIMELY_API_TOKEN` | OAuth access token or personal token with `projects`, `events`, and `forecasts` scopes. |
   | `TIMELY_DEFAULT_WINDOW_DAYS` | Optional lookback window (defaults to 30). |

3. **Export a report**
   ```bash
   timely-tracker export --since 2024-01-01 --upto 2024-12-31 -o reports/timely-burndown.xlsx
   ```

   If you omit `--since/--upto`, the tool uses the default rolling window from `TIMELY_DEFAULT_WINDOW_DAYS`.

## Output

The Excel file contains:

- Project/task worksheet with columns `Project ID`, `Project`, `Task Code`, `Task Name`, `Logged Hours`, `Budget Hours`, and `Hours Remaining`.
- Project summary worksheet with the same metrics rolled up per project.

These sheets can be imported into Power BI or shared directly.

## Development

- Run `ruff check .` and `pytest` after making code changes.
- The CLI entry point `timely_tracker/cli.py` wires together configuration, API access, aggregation, and Excel export. Extend those modules to add new fields or alternative outputs.

## Notes & Limitations

- The tool currently relies on the Timely Forecasts API for task budgets. If you do not use forecasts, the Excel sheet will list logged hours but budget/remaining columns will be blank.
- Timely rate limiting is respected implicitly by paginating requests (200 records per page). For very large accounts consider adding sleep/retry logic.
- OAuth tokens expire; refresh them before rerunning the report if you see 401 responses.
