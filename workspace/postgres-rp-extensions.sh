#!/bin/bash
set -e

echo "‣ Loading hstore extension..."
psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "CREATE EXTENSION IF NOT EXISTS hstore;" >/dev/null 2>&1
echo "‣ Loading uuid-ossp extension..."
psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";" >/dev/null 2>&1
