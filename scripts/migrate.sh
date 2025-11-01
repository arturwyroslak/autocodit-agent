#!/bin/bash
set -euo pipefail

# Apply init and schema SQL to Postgres container via psql
DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-autocodit}"
DB_NAME="${DB_NAME:-autocodit_agent}"

echo "Waiting for Postgres at $DB_HOST:$DB_PORT..."
until PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d postgres -c "\l" >/dev/null 2>&1; do
  sleep 2
  echo -n "."
done

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

echo -e "\nApplying database init.sql and schema parts..."
psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 -f "$ROOT_DIR/database/init.sql"

for part in "$ROOT_DIR/database/schema.part1.sql" \
            "$ROOT_DIR/database/schema.part2.sql" \
            "$ROOT_DIR/database/schema.part3.sql"; do
  if [[ -f "$part" ]]; then
    echo "Applying $(basename "$part")..."
    psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 -f "$part"
  else
    echo "Missing $part" >&2
    exit 1
  fi
done

echo "Database migrations applied successfully."
