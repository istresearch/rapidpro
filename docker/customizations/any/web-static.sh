#!/bin/bash

source /venv/bin/activate

if [[ -z $DATABASE_URL ]]; then
  export DATABASE_URL=postgres://bla
fi
if [[ -z $SECRET_KEY ]]; then
  export SECRET_KEY=123
fi

set -ex # fail on any error & print commands as they're run

if [[ -n $REDIS_URL ]]; then
  echo 'Clearing static cache...'
  python clear-compressor-cache.py
  echo 'Finished clearing static cache.'
fi

echo 'Collecting compressed static website files...'
python manage.py collectstatic --noinput --settings=temba.settings_collect_static

echo 'Compressing static website files...'
python manage.py compress --extension=".haml" --force -v0 --settings=temba.settings_compress_static
echo 'Finished compressing static website files.'
