"""Thin Timely API client."""
from __future__ import annotations

from datetime import date
from typing import Any, Dict, Iterable, Iterator, List, Optional

import requests
from requests import Response

from .config import TimelySettings


class TimelyApiError(RuntimeError):
    """Raised when the Timely API returns an error response."""

    def __init__(self, response: Response):
        self.response = response
        detail = _safe_json(response)
        super().__init__(
            f"Timely API error {response.status_code}: {detail if detail else response.text}"
        )


def _safe_json(response: Response) -> Any:
    try:
        return response.json()
    except ValueError:
        return None


class TimelyClient:
    """Small helper around the Timely REST endpoints we need."""

    def __init__(self, settings: TimelySettings):
        self.settings = settings
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {settings.api_token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        )

    def _url(self, path: str) -> str:
        return f"{self.settings.base_url}/{self.settings.account_id}{path}"

    def _request(self, method: str, path: str, *, params: Optional[Dict[str, Any]] = None) -> Any:
        response = self.session.request(method, self._url(path), params=params, timeout=30)
        if response.status_code >= 400:
            raise TimelyApiError(response)
        return _safe_json(response)

    def list_projects(self) -> List[Dict[str, Any]]:
        return self._request("GET", "/projects") or []

    def iter_events(
        self,
        *,
        since: Optional[date] = None,
        upto: Optional[date] = None,
        per_page: int = 200,
        include_unlogged: bool = False,
    ) -> Iterator[Dict[str, Any]]:
        params: Dict[str, Any] = {
            "per_page": per_page,
            "filter": "all" if include_unlogged else "logged",
        }
        if since:
            params["since"] = since.isoformat()
        if upto:
            params["upto"] = upto.isoformat()
        yield from self._paginate("/events", params=params)

    def iter_forecasts(
        self,
        *,
        since: Optional[date] = None,
        upto: Optional[date] = None,
        per_page: int = 200,
    ) -> Iterator[Dict[str, Any]]:
        params: Dict[str, Any] = {
            "per_page": per_page,
        }
        if since:
            params["since"] = since.isoformat()
        if upto:
            params["upto"] = upto.isoformat()
        yield from self._paginate("/forecasts", params=params)

    def _paginate(
        self, path: str, *, params: Optional[Dict[str, Any]] = None
    ) -> Iterator[Dict[str, Any]]:
        params = params.copy() if params else {}
        page = 1
        per_page = int(params.get("per_page", 100))
        while True:
            params["page"] = page
            payload = self._request("GET", path, params=params) or []
            if not isinstance(payload, list):
                payload = payload.get("data", [])  # pragmatic fallback
            if not payload:
                break
            for record in payload:
                yield record
            if len(payload) < per_page:
                break
            page += 1

    def close(self) -> None:
        self.session.close()

    def __enter__(self) -> "TimelyClient":
        return self

    def __exit__(self, *exc_info: Any) -> None:
        self.close()
