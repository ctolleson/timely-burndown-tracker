"""Configuration helpers for Timely tracker."""
from __future__ import annotations

import os
from datetime import date, timedelta
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError

load_dotenv()


class TimelySettings(BaseModel):
    """Runtime configuration sourced from environment variables."""

    account_id: str = Field(alias="TIMELY_ACCOUNT_ID", min_length=1)
    api_token: str = Field(alias="TIMELY_API_TOKEN", min_length=1)
    base_url: str = Field(default="https://api.timelyapp.com/1.1")
    default_window_days: int = Field(default=30, ge=1, le=365)

    model_config = {
        "populate_by_name": True,
    }

    @classmethod
    def from_env(cls) -> "TimelySettings":
        try:
            return cls(
                **{
                    "TIMELY_ACCOUNT_ID": os.getenv("TIMELY_ACCOUNT_ID", "").strip(),
                    "TIMELY_API_TOKEN": os.getenv("TIMELY_API_TOKEN", "").strip(),
                    "base_url": os.getenv("TIMELY_BASE_URL", "https://api.timelyapp.com/1.1").rstrip("/"),
                    "default_window_days": int(os.getenv("TIMELY_DEFAULT_WINDOW_DAYS", "30")),
                }
            )
        except (ValidationError, ValueError) as exc:  # pragma: no cover - defensive
            missing = []
            if not os.getenv("TIMELY_ACCOUNT_ID"):
                missing.append("TIMELY_ACCOUNT_ID")
            if not os.getenv("TIMELY_API_TOKEN"):
                missing.append("TIMELY_API_TOKEN")
            hint = (
                "Missing required environment variables: " + ", ".join(missing)
                if missing
                else "Invalid Timely configuration"
            )
            raise RuntimeError(f"{hint}: {exc}") from exc

    def resolve_since(self, since: Optional[date]) -> date:
        if since:
            return since
        return date.today() - timedelta(days=self.default_window_days)

    def resolve_upto(self, upto: Optional[date]) -> date:
        if upto:
            return upto
        return date.today()
