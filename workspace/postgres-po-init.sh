#!/bin/bash
set -e

if [[ -z $POSTOFFICE_DB ]]; then
  POSTOFFICE_DB="postoffice"
fi

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
	    CREATE DATABASE $POSTOFFICE_DB;
	    GRANT ALL PRIVILEGES ON DATABASE $POSTOFFICE_DB TO $POSTGRES_USER;
EOSQL

echo "‣ Loading uuid-ossp extension..."
psql -U $POSTGRES_USER -d $POSTOFFICE_DB -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";" >/dev/null 2>&1
