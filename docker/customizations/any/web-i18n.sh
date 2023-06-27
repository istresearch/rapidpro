#!/bin/bash

source /venv/bin/activate

if [[ -z $DATABASE_URL ]]; then
  export DATABASE_URL=postgres://bla
fi
if [[ -z $SECRET_KEY ]]; then
  export SECRET_KEY=123
fi

# remove any pre-compiled translations
find locale -name '*.mo' -type f -delete

echo ''
echo 'Ensure translations are compiled…'
python manage.py compilemessages
echo 'Finished compiling translations.'
