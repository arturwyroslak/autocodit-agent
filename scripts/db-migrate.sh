#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

if [[ -f "${SCRIPT_DIR}/migrate.sh" ]]; then
  bash "${SCRIPT_DIR}/migrate.sh"
else
  echo "scripts/migrate.sh not found" >&2
  exit 1
fi
