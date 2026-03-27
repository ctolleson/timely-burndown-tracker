"""Command-line entrypoints."""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Optional

import typer

from .api import TimelyClient
from .config import TimelySettings
from .excel import export_rollups_to_excel
from .tracker import aggregate_rollups

app = typer.Typer(add_completion=False, help="Generate Excel burndown reports from Timely data.")


@app.command("export")
def export_command(
    output: Path = typer.Option(
        Path("reports/timely-projects.xlsx"),
        "--output",
        "-o",
        help="Destination .xlsx file for the burndown report.",
    ),
    since: Optional[date] = typer.Option(
        None,
        help="Inclusive start date for pulling Timely events/forecasts (defaults to TIMELY_DEFAULT_WINDOW_DAYS).",
    ),
    upto: Optional[date] = typer.Option(
        None,
        help="Inclusive end date for pulling Timely events/forecasts (defaults to today).",
    ),
    prefix_len: int = typer.Option(4, help="Number of leading characters from each comment that define the task code."),
    include_forecasts: bool = typer.Option(
        True,
        help="Use Timely forecast estimates to calculate per-task budgets.",
    ),
    include_unlogged: bool = typer.Option(
        False,
        help="Include draft/unlogged events when summing usage.",
    ),
) -> None:
    """Export an Excel burndown report using Timely projects, events, and task budgets."""

    settings = TimelySettings.from_env()
    resolved_since = settings.resolve_since(since)
    resolved_upto = settings.resolve_upto(upto)

    typer.echo(
        f"Pulling Timely data from {resolved_since.isoformat()} through {resolved_upto.isoformat()}..."
    )

    with TimelyClient(settings) as client:
        projects = client.list_projects()
        events = list(
            client.iter_events(
                since=resolved_since,
                upto=resolved_upto,
                include_unlogged=include_unlogged,
            )
        )
        forecasts = (
            list(client.iter_forecasts(since=resolved_since, upto=resolved_upto))
            if include_forecasts
            else []
        )

    typer.echo(
        f"Found {len(projects)} project(s), {len(events)} event(s), {len(forecasts)} forecast(s)."
    )

    rollups = aggregate_rollups(
        projects=projects,
        events=events,
        forecasts=forecasts,
        prefix_len=prefix_len,
    )

    path = export_rollups_to_excel(rollups, output)
    typer.echo(f"Report saved to {path}")


def main() -> None:  # pragma: no cover - convenience entry point
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
