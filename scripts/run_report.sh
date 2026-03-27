#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -f "${ROOT_DIR}/.env" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "${ROOT_DIR}/.env"
  set +a
fi

if [[ -z "${TIMELY_ACCOUNT_ID:-}" ]]; then
  echo "TIMELY_ACCOUNT_ID is not set. Update .env before running." >&2
  exit 1
fi

if [[ -z "${TIMELY_API_TOKEN:-}" ]]; then
  echo "TIMELY_API_TOKEN is not set. Update .env before running." >&2
  exit 1
fi

VENVBIN="${ROOT_DIR}/.venv/bin"
if [[ ! -x "${VENVBIN}/timely-tracker" ]]; then
  echo "timely-tracker CLI not found. Did you run 'pip install -e .' in ${ROOT_DIR}? " >&2
  exit 1
fi

if [[ "$#" -gt 0 ]]; then
  CMD=("${VENVBIN}/timely-tracker" export "$@")
else
  SINCE="${REPORT_SINCE:-}"
  UPTO="${REPORT_UPTO:-}"
  OUTPUT="${REPORT_OUTPUT:-${ROOT_DIR}/reports/timely-burndown.xlsx}"
  CMD=("${VENVBIN}/timely-tracker" export "-o" "${OUTPUT}")
  if [[ -n "${SINCE}" ]]; then
    CMD+=("--since" "${SINCE}")
  fi
  if [[ -n "${UPTO}" ]]; then
    CMD+=("--upto" "${UPTO}")
  fi
fi

echo "Running: ${CMD[*]}"
exec "${CMD[@]}"
