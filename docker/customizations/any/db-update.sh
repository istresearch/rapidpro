#!/bin/bash

set -e # fail on any error & print commands as they're run

source /venv/bin/activate

#------
set +x  # make sure the password isn't echoed to stdout
echo "*:*:*:*:$(echo \"${DATABASE_URL}\" | cut -d'@' -f1 | cut -d':' -f3)" > ${HOME}/.pgpass
chmod 0600 "${HOME}/.pgpass"
trap 'rm '"${HOME}"'/.pgpass' EXIT
set -x

#------
# initialize/update the db schema
echo "Updating db schema..."
# migrate must be called to create initial db schema
python manage.py migrate
echo "Finished updating db schema."
