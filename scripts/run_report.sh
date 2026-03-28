#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

show_usage() {
  cat <<'EOF'
Usage:
  ./scripts/run_report.sh [timely-tracker export options]

Examples:
  ./scripts/run_report.sh --since 2025-01-01 --upto 2025-12-31 -o reports/2025.xlsx
  REPORT_SINCE=2025-01-01 REPORT_OUTPUT=reports/latest.xlsx ./scripts/run_report.sh

This wrapper always calls:
  timely-tracker export --include-unlogged [...]

Common options forwarded to the CLI:
  --since YYYY-MM-DD         Set the inclusive start date (default 2025-01-01)
  --upto YYYY-MM-DD          Set the inclusive end date (default today)
  --output, -o PATH          Excel destination (default reports/timely-burndown.xlsx)
  --prefix-len N             Comment prefix length used for task codes (default 4)
  --include-forecasts / --no-include-forecasts

Environment variables you can set before running:
  REPORT_SINCE, REPORT_UPTO, REPORT_OUTPUT  (used only when no CLI args)

Pass any additional arguments exactly as you would to `timely-tracker export`.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  show_usage
  exit 0
fi

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
SITE_PKGS="${ROOT_DIR}/.venv/lib/python3.12/site-packages"

if [[ -d "${SITE_PKGS}" ]]; then
  chflags -R nohidden "${SITE_PKGS}" 2>/dev/null || true
fi

if [[ ! -x "${VENVBIN}/timely-tracker" ]]; then
  echo "timely-tracker CLI not found. Did you run 'pip install -e .' in ${ROOT_DIR}? " >&2
  exit 1
fi

if [[ "$#" -gt 0 ]]; then
  CMD=("${VENVBIN}/timely-tracker" export --include-unlogged "$@")
else
  SINCE="${REPORT_SINCE:-}"
  UPTO="${REPORT_UPTO:-}"
  OUTPUT="${REPORT_OUTPUT:-${ROOT_DIR}/reports/timely-burndown.xlsx}"
  CMD=("${VENVBIN}/timely-tracker" export "--include-unlogged" "-o" "${OUTPUT}")
  if [[ -n "${SINCE}" ]]; then
    CMD+=("--since" "${SINCE}")
  fi
  if [[ -n "${UPTO}" ]]; then
    CMD+=("--upto" "${UPTO}")
  fi
fi

echo "Running: ${CMD[*]}"
exec "${CMD[@]}"
