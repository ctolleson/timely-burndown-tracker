#!/usr/bin/env python3
"""Dump raw Timely API payloads to logs for debugging."""
from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path
from typing import Optional

from timely_tracker.api import TimelyClient
from timely_tracker.config import TimelySettings


def _parse_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    return date.fromisoformat(value)


def main() -> None:
    settings = TimelySettings.from_env()
    env_since = _parse_date(os.getenv("REPORT_SINCE"))
    env_upto = _parse_date(os.getenv("REPORT_UPTO"))
    since = settings.resolve_since(env_since)
    upto = settings.resolve_upto(env_upto)

    with TimelyClient(settings) as client:
        payload = {
            "since": since.isoformat(),
            "upto": upto.isoformat(),
            "projects": client.list_projects(),
            "events": list(client.iter_events(since=since, upto=upto, include_unlogged=True)),
            "forecasts": list(client.iter_forecasts(since=since, upto=upto)),
        }

    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"timely-api-{upto.isoformat()}.json"
    with log_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)

    print(f"Wrote Timely payload log to {log_path}")


if __name__ == "__main__":
    main()
