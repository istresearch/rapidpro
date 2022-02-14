#!/bin/sh

set -e # fail on any error & print commands as they're run

source /venv/bin/activate

#------
set +x  # make sure the password isn't echoed to stdout
echo "*:*:*:*:$(echo \"$DATABASE_URL\" | cut -d'@' -f1 | cut -d':' -f3)" > $HOME/.pgpass
chmod 0600 $HOME/.pgpass
trap "rm $HOME/.pgpass" EXIT
set -x

#------
echo "Verify code models vs db schema..."
python manage.py makemigrations
