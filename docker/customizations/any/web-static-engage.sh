#!/bin/bash

# fail on any error & print commands as they're run
set -ex
source /venv/bin/activate

if [[ -z $DATABASE_URL ]]; then
  export DATABASE_URL=postgres://bla
fi
if [[ -z $SECRET_KEY ]]; then
  export SECRET_KEY=123
fi

echo 'Collecting static website files in engage/static/engage…'
SETTINGS_FILE=temba/local_settings.py
echo "from django.conf import settings" > "${SETTINGS_FILE}"
echo "import os" >> "${SETTINGS_FILE}"
echo "PROJECT_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)))" >> "${SETTINGS_FILE}"
echo "STATICFILES_DIRS = (os.path.join(PROJECT_DIR, '../engage/static/engage'),)" >> "${SETTINGS_FILE}"
python manage.py collectstatic --noinput --settings=temba.settings
rm temba/local_settings.py
echo ""  # ensure we end up on fresh line
echo 'Finished compressing static website files.'
