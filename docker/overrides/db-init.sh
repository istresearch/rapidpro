#!/bin/sh

set -e # fail on any error & print commands as they're run

source /venv/bin/activate

#------
# ensure db server has needed functions/extensions
set +x  # make sure the password isn't echoed to stdout
echo "*:*:*:*:$(echo \"$DATABASE_URL\" | cut -d'@' -f1 | cut -d':' -f3)" > $HOME/.pgpass
chmod 0600 $HOME/.pgpass
trap "rm $HOME/.pgpass" EXIT
set -x

echo "Creating db schema..."
python manage.py dbshell < init_db.sql
echo "Finished creating db schema."

#------
# initialize/update the db schema
echo "Updating db schema..."
# migrate must be called to create initial db schema
python manage.py migrate
# however, not all schema updates made it to the "initialization" code
python manage.py makemigrations
# makemigrations requires a re-run of "migrate"
python manage.py migrate
echo "Finished updating db schema."
