#!/bin/bash

source /venv/bin/activate

if [[ -z $DATABASE_URL ]]; then
  export DATABASE_URL=postgres://bla
fi
if [[ -z $SECRET_KEY ]]; then
  export SECRET_KEY=123
fi

echo ''
echo 'Ensure translations are compiled…'
python manage.py compilemessages --settings=temba.settings
echo 'Finished compiling translations.'

####
#8 8.726 CommandError: Can't find msgfmt. Make sure you have GNU gettext tools 0.15 or newer installed.
#
