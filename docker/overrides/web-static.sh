#!/bin/sh

source venv/bin/activate

if [[ -z $REDIS_URL ]]; then
  export REDIS_URL=redis://redis
fi
if [[ -z $DATABASE_URL ]]; then
  export DATABASE_URL=postgres://bla
fi
if [[ -z $SECRET_KEY ]]; then
  export SECRET_KEY=123
fi

PATH=node_modules/coffeescript/bin:$PATH

set -ex # fail on any error & print commands as they're run

echo 'Clearing compressor cache...'
python clear-compressor-cache.py
echo 'Finished clearing compressor cache.'

echo 'Compressing static website files...'
python manage.py compress --extension=".haml" --force -v0
echo 'Finished compressing static website files.'

echo 'Collecting compressed static website files...'
python manage.py collectstatic --noinput --no-post-process
echo 'Finished collecting compressed static website files.'
