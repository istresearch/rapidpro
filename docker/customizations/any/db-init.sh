#!/bin/bash

set -e # fail on any error & print commands as they're run

source /venv/bin/activate

#------
# ensure db server has needed functions/extensions
set +x  # make sure the password isn't echoed to stdout
PGPW=$(echo "${DATABASE_URL}" | cut -d'@' -f1 | cut -d':' -f3)
echo "*:*:*:*:${PGPW}" > "${HOME}/.pgpass"
chmod 0600 "${HOME}/.pgpass"
trap 'rm '"${HOME}"'/.pgpass' EXIT
set -x

echo "Creating db schema..."
python manage.py dbshell < init_db.sql
if [[ "${DATABASE_URL}" =~ .+\.rds\.amazonaws\.com.* ]]; then
  python manage.py dbshell < init_rds_db.sql
fi
echo "Finished creating db schema."

#------
# initialize/update the db schema
echo "Updating db schema..."
# migrate must be called to create initial db schema
python manage.py migrate
echo "Finished updating db schema."
