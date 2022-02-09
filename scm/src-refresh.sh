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
# Once you have your volume mounts added, you just need to run
# two commands to refresh your docker container to use your newly
# modified code. First, execute this script in the container:
#
# $ docker-compose exec engage /opt/dev/src-refresh.sh
#
# then restart the container itself, e.g.
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
