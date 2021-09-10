#!/bin/sh

set -ex # fail on any error & print commands as they're run

echo 'Clearing compressor cache...'
/venv/bin/python clear-compressor-cache.py
echo 'Finished clearing compressor cache.'

echo 'Compressing static website files...'
/venv/bin/python manage.py compress --extension=".haml" --force -v0
echo 'Finished compressing static website files.'

echo 'Collecting compressed static website files...'
/venv/bin/python manage.py collectstatic --noinput --no-post-process
echo 'Finished collecting compressed static website files.'
