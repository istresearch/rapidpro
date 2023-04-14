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
  echo 'Clearing static cache…'
  python clear-compressor-cache.py
  echo 'Finished clearing static cache.'
fi

echo 'Collecting compressed static website files…'
python manage.py collectstatic --noinput --settings=temba.settings

echo "Compressing static website files…"

#echo "use Brotli compression to make .br files in CACHE directory"
export COMPRESS_WITH_BROTLI=on; python manage.py compress --extension=".haml" --force -v0 --settings=temba.settings_compress_static
#echo "use Gzip compression to make .gz files in CACHE directory"
export COMPRESS_WITH_BROTLI=off; python manage.py compress --extension=".haml" --force -v0 --settings=temba.settings_compress_static
#echo "add new compressed files to whitenoise: manifest.json, manifest.json.gz, manifest.json.br"
## --no-post-process option is to tell whitenoise not to compress static files again.
python manage.py collectstatic --noinput --settings=temba.settings --no-post-process

echo 'Finished compressing static website files.'
