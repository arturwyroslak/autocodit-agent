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

echo "\nApplying database init.sql and schema.sql..."
psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 -f /app/database/init.sql
psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 -f /app/database/schema.sql

echo "Database migrations applied successfully."
