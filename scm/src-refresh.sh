#!/bin/bash

####################################################################
# Basic usage:
#
# Volume mount this file so it can be run from inside the container.
# - /DevCode/rapidpro/scm:/opt/dev/src-refresh.sh
#
# Mount the base webapp folders you wish to update while working.
# NOTE: these are entirely optional and discouraged, but possible.
# Mount the folders from the base webapp to /opt/dev/rp/<folder>.
# - /DevCode/rapidpro/temba:/opt/dev/rp/temba
# - /DevCode/rapidpro/templates:/opt/dev/rp/templates
# - /DevCode/rapidpro/static:/opt/dev/rp/static
# etc., etc.
#
# Required: mount docker/customizations/any to /opt/dev/any
# - /DevCode/rapidpro/docker/customizations/any:/opt/dev/any
#
# Required: mount docker/customizations/<brand> to /opt/dev/brand
# - /DevCode/rapidpro/docker/customizations/engage:/opt/dev/brand
#
# Once you have your volume mounts added, you just need to restart
# the container itself whenever you want update your browser view.
# The restart script will copy over the "any" and "brand" flavor
# code as well as re-collect the static files for you. e.g.
#
# $ docker-compose restart engage
#
####################################################################

SRC=/opt/dev/rp
# refresh src folders
if [ -d "$SRC" ]; then
  for item in "${SRC%*/}"/*/; do
    # if what is found is a directory and not a symlink
    if [[ -d "$item" && ! -L "$item" ]]; then
      echo "Refreshing webapp src: `basename ${item}`"
      rsync -a "${item}" "/rapidpro/`basename ${item}`"
    fi
  done
fi

# overlap "any"
SRC=/opt/dev/any
if [ -d "$SRC" ]; then
  echo "Refreshing 'any' customizations"
  rsync -a "${SRC}/" /rapidpro/
fi

# overlap brand
SRC=/opt/dev/brand
if [ -d "$SRC" ]; then
  echo "Refreshing brand customizations"
  rsync -a "${SRC}/" /rapidpro/
fi

if [[ $DEV_CODE_ONLY != "1" ]]; then
  # re-collect all the sitestatic assets
  echo "Refreshing static files"
  if [[ $CLEAR_SITESTATIC == "1" ]]; then
    rm -R /rapidpro/sitestatic/*
  fi
  source /venv/bin/activate; REDIS_URL=redis://redis DATABASE_URL=postgres://bla SECRET_KEY=123 \
      python manage.py collectstatic --no-input --settings=temba.settings_collect_static
fi