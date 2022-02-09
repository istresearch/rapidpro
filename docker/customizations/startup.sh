#!/bin/sh
set -ex # fail on any error & print commands as they're run

source /venv/bin/activate

echo 'MANAGEPY_COLLECTSTATIC?'; if [ "x$MANAGEPY_COLLECTSTATIC" = "xon" ]; then
	mkdir -p /rapidpro/static/sitestatic
	cp -fr /rapidpro/static/brands /rapidpro/static/sitestatic/brands
	python manage.py collectstatic --noinput --no-post-process
fi
echo 'CLEAR_COMPRESSOR_CACHE?'; if [ "x$CLEAR_COMPRESSOR_CACHE" = "xon" ]; then
	python clear-compressor-cache.py
fi
echo 'MANAGEPY_COMPRESS?'; if [ "x$MANAGEPY_COMPRESS" = "xon" ]; then
	python manage.py compress --extension=".haml" --force -v0
fi
echo 'MANAGEPY_INIT_DB?'; if [ "x$MANAGEPY_INIT_DB" = "xon" ]; then
	set +x  # make sure the password isn't echoed to stdout
	echo "*:*:*:*:$(echo \"$DATABASE_URL\" | cut -d'@' -f1 | cut -d':' -f3)" > $HOME/.pgpass
	set -x
	chmod 0600 $HOME/.pgpass
	python manage.py dbshell < init_db.sql
	rm $HOME/.pgpass
fi
echo 'MANAGEPY_MIGRATE?'; if [ "x$MANAGEPY_MIGRATE" = "xon" ]; then
	python manage.py migrate
fi
echo 'MANAGEPY_IMPORT_GEOJSON?'; if [ "x$MANAGEPY_IMPORT_GEOJSON" = "xon" ]; then
	echo "Downloading geojson for relation_ids $OSM_RELATION_IDS"
	python manage.py download_geojson $OSM_RELATION_IDS
	python manage.py import_geojson ./geojson/*.json
	echo "Imported geojson for relation_ids $OSM_RELATION_IDS"
fi

echo 'run celery or rapidpro?';
TYPE=${1:-rapidpro}
if [ "$TYPE" = "celery" ]; then
	$CELERY_CMD
elif [ "$TYPE" = "rapidpro" ]; then
  if [ -f /opt/dev/src-refresh.sh ]; then
    /opt/dev/src-refresh.sh
  fi
  echo 'MANAGEPY_STARTUP_TASKS?' ; if [ "x$MANAGEPY_STARTUP_TASKS" = "xon" ]; then
	  python /rapidpro/startup.py
  fi
	$STARTUP_CMD
fi
