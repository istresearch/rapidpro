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
echo "STATICFILES_DIRS = (os.path.join(PROJECT_DIR, "engage/static/engage"))" > temba.local_settings.py
python manage.py collectstatic --noinput --settings=temba.settings
rm temba.local_settings.py
echo ""  # ensure we end up on fresh line
echo 'Finished compressing static website files.'
