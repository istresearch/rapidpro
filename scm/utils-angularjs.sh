#!/bin/bash

#####################
# Utilities that are helpful for an SCM script that builds phpBitsTheater apps.
# REQUIRES: utils.sh to be sourced in addition to this script.
#####################

if [ "$0" = "$BASH_SOURCE" ]; then
    echo "Error: Script must be sourced"
    exit 1
fi

####################
# Update the UI project with new version info.
# @param string $1 - path to project.
# @param string $2 - human version.
# @param string $3 - numeric version.
# @param string $4 - api version (numeric).
function BumpUIProjectVersion
{
  local PATH_TO_PROJECT=$1
  local VERSION_STR=$2
  local VERSION_NUM=$3
  local VERSION_API=$4
  echo "${VERSION_STR}" > "${PATH_TO_PROJECT}/src/resources/version.txt"
  echo "${VERSION_API}" > "${PATH_TO_PROJECT}/src/resources/api-seq.txt"
}

####################
# Verify the UI project with specified version info.
# @param string $1 - path to project.
# @param string $2 - human version.
# @param string $3 - numeric version.
# @param string $4 - api version (numeric).
function VerifyUIProjectVersion
{
  local PATH_TO_PROJECT=$1
  local VERSION_STR=$2
  local VERSION_NUM=$3
  local VERSION_API=$4

  local FILE_PATH="${PATH_TO_PROJECT}/src/resources/version.txt"
  if [[ ! -f ${FILE_PATH} ]]; then
    exit 4
  elif [[ -z $(grep "${VERSION_STR}" "${FILE_PATH}") ]]; then
    exit 1
  fi

  local FILE_PATH="${PATH_TO_PROJECT}/src/resources/api-seq.txt"
  if [[ ! -f ${FILE_PATH} ]]; then
    exit 4
  elif [[ -z $(grep "${VERSION_API}" "${FILE_PATH}") ]]; then
    exit 3
  fi
}

####################
# Print error message for non-validating project.
# @param string $1 - path to project.
# @param string $2 - the fail value of Verify.
function FailUIProjectVersion
{
  local PATH_TO_PROJECT=$1
  local FAIL_NUM=$2
  local COMPONENT_NAME="$(basename ${PATH_TO_PROJECT})"
  case $FAIL_NUM in
    4) PrintPaddedTextRight "version.txt or api-seq.txt files" "NOT FOUND" ${COLOR_MSG_WARNING} ;;
    1) PrintPaddedTextRight "${COMPONENT_NAME} version str" "DID NOT MATCH" ${COLOR_MSG_WARNING} ;;
    2) PrintPaddedTextRight "${COMPONENT_NAME} version num" "DID NOT MATCH" ${COLOR_MSG_WARNING} ;;
    3) PrintPaddedTextRight "${COMPONENT_NAME} API version num" "DID NOT MATCH" ${COLOR_MSG_WARNING} ;;
  esac
}

