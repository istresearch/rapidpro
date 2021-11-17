#!/bin/bash

#####################
# Utilities that are helpful for any SCM script we may wish to create.
#####################

if [ "$0" = "$BASH_SOURCE" ]; then
    echo "Error: Script must be sourced"
    exit 1
fi

# https://misc.flogisoft.com/bash/tip_colors_and_formatting
# Colors! :D
export COLOR_NONE="\033[0m" \
    COLOR_CYAN="\033[0;96m" \
    COLOR_YELLOW="\033[0;33m" \
    COLOR_BOLD="\033[1m" \
    COLOR_UNBOLD="\033[21m" \
    COLOR_DIM="\033[2m"
# Once colors have been defined, we can use them for specific things.
export COLOR_MSG=${COLOR_CYAN} \
    COLOR_MSG_INFO=${COLOR_YELLOW} \
    COLOR_MSG_IMPORTANT="\033[1;96m" \
    COLOR_MSG_WARNING="\033[1;93m"

# used when performing SSH operations
export SSH_ARGS="-q -o BatchMode=yes -o ConnectTimeout=5"

# uniform timestamp, if needed
export AUTOBUILD_DATETIME_STAMP=$(date +%Y%m%d-%H%M%S)

# use CircleCI working directory, if defined, as REPO_PATH
if [[ -n ${CIRCLE_WORKING_DIRECTORY} ]]; then
  export REPO_PATH=$(realpath "${CIRCLE_WORKING_DIRECTORY/#\~/$HOME}")
fi
if [[ -z ${REPO_PATH} ]]; then
  export REPO_PATH="${PWD}"
fi
# if Workspace path is not defined, use '${REPO_PATH}/workspace'
if [[ -z ${WORKSPACE} ]]; then
  export WORKSPACE="${REPO_PATH}/workspace"
fi
# if Artifact path is not defined, use '${REPO_PATH}/artifacts'
if [[ -z ${ARTIFACT_PATH} ]]; then
  export ARTIFACT_PATH="${REPO_PATH}/artifacts"
  mkdir -p "${ARTIFACT_PATH}"
fi

# dependent GitHub repos will be cloned here
export GITHUB_REPO_PATH=${WORKSPACE}

# get current branch name
if [[ -z "${BRANCH_NAME}" ]]; then
  if [[ -n "${CIRCLE_BRANCH}" ]]; then
    export BRANCH_NAME="${CIRCLE_BRANCH}"
  else
    export BRANCH_NAME=$(git branch | grep -e "^*" | cut -d' ' -f 2)
  fi
fi


function PrintPaddedText
{
  local ALIGNMENT=$1
  local MESSAGE=$2
  local MESSAGE_VALUE=$3
  local PAD_LENGTH
  case ALIGNMENT in
    "left"|"Left"|"LEFT")
      PAD_LENGTH=$(( 40 - ${#MESSAGE} ))
      ;;
    *)
      PAD_LENGTH=$(( 80 - ${#MESSAGE} - ${#MESSAGE_VALUE} - 2 ))
      ;;
  esac
  local PAD_INSERT=$(printf '%*s' "${PAD_LENGTH}" " ")
  echo -e "${MESSAGE}${PAD_INSERT}[${MESSAGE_VALUE}]"
}

function PrintPaddedTextLeft
{
  local MESSAGE=$1
  local MESSAGE_VALUE=$2
  local VALUE_COLOR=$3
  if [[ -n ${VALUE_COLOR} ]] ; then
    if [[ ${VALUE_COLOR} == "\033["* ]] ; then
      MESSAGE_VALUE="${VALUE_COLOR}${MESSAGE_VALUE}${COLOR_NONE}"
    else
      MESSAGE_VALUE="\033[${VALUE_COLOR}m${MESSAGE_VALUE}${COLOR_NONE}"
    fi
  fi
  PrintPaddedText "left" "${MESSAGE}" "${MESSAGE_VALUE}"
}

function PrintPaddedTextRight
{
  local MESSAGE=$1
  local MESSAGE_VALUE=$2
  local VALUE_COLOR=$3
  if [[ -n ${VALUE_COLOR} ]] ; then
    if [[ ${VALUE_COLOR} == "\033["* ]] ; then
      MESSAGE_VALUE="${VALUE_COLOR}${MESSAGE_VALUE}${COLOR_NONE}"
    else
      MESSAGE_VALUE="\033[${VALUE_COLOR}m${MESSAGE_VALUE}${COLOR_NONE}"
    fi
  fi
  PrintPaddedText "right" "${MESSAGE}" "${MESSAGE_VALUE}"
}

#********************************
# SSH into a remote server and check to see if a file exists.
# @param string $1 - the SSH host to check.
# @param string $2 - the file path to check.
# @return string Returns "OK" if remote file exists.
function SpotCheckRemoteFile
{
  ssh ${SSH_ARGS} "$1" "[ -f $2 ] && echo OK"
}

#********************************
# SSH into a remote server and check to see if a directory exists.
# @param string $1 - the SSH host to check.
# @param string $2 - the directory to check.
# @return string Returns "OK" if remote directory exists.
function SpotCheckRemotePath
{
  ssh ${SSH_ARGS} "$1" "[ -d $2 ] && echo OK"
}

#********************************
# SSH into a remote server and check to see if a link exists.
# @param string $1 - the SSH host to check.
# @param string $2 - the link to check.
# @return string Returns "OK" if remote link exists.
function SpotCheckRemoteLink
{
  ssh ${SSH_ARGS} "$1" "[ -h $2 ] && echo OK"
}

##################
# Send a message to possible Slack integration.
# @param $1 - the exit code to check (0=Success)
# @param $2 - the success/fail message
function checkError
{
  local EXIT_CODE=$1
  local DESC=$2
  echo
  if [[ ${EXIT_CODE} -ne 0 ]]; then
    echo "ERROR: $DESC"
    exit 1
  else
    echo "DONE: $DESC"
  fi
}

####################
# @return Returns X rounded to the nearest Y.
function GetXRoundedToNearestY
{
  echo $(( (($1 + ($2/2)) / $2)*$2 ))
}

####################
# @return Returns X rounded down to the nearest Y.
function GetXRoundedDownToY
{
  echo $(( (($1 + ($2)) / $2)*$2 ))
}

####################
# @return Returns X rounded up to the nearest Y.
function GetXRoundedUpToY
{
  echo $(( (($1 + ($2 - 1)) / $2)*$2 ))
}

#########################################################################
# Create the release prep branch.
# @param $1 the name to use for the branch.
function ConstructReleasePrepBranch
{
  local BRANCH_NAME=$1
  local BRANCH_HASH
  git fetch
  git checkout develop
  git pull origin develop
  BRANCH_HASH=$(git rev-parse --quiet --verify ${BRANCH_NAME})
  if [[ -z ${BRANCH_HASH} ]] ; then
    # The prep branch didn't exist. Create it, and push it upward.
    git checkout -b ${BRANCH_NAME}
    # In case we've done this before, see if remote has this branch already.
    git pull origin ${BRANCH_NAME} 2> /dev/null
    if [[ -z ${IS_TEST_RUN} ]] ; then
      git push -u origin ${BRANCH_NAME}
    fi
  else
    # The branch existed from a previous run. Switch to it, and update it.
    git checkout ${BRANCH_NAME}
    git pull origin ${BRANCH_NAME}
  fi
}

####################
# Trigger a CircleCI build in a different project (repo).
# @param string $1 - project name (URL segment for CircleCI API call).
# @param string $2 - the branch name of the project build to trigger (URL segment).
# @param string $3 - JSON string of extra parameters for the triggered build.
#   NOTE USING $3: v1 does NOT handle workflows and therefore no context, YOU HAVE BEEN WARNED!
#   NOTE: use v1.1 with Artifacts if you need build params with workflow context builds!
# @ENV oCI_API_TOKEN - the required API token used to call CircleCI's API
# @ENV oCI_ORG - (OPTIONAL) the org name for the project to trigger. Default: "istresearch"
# @ENV BUILD_INFO - the results of the curl command, if desired.
function TriggerCircleCIProjectBuild
{
  if [[ -z ${oCI_ORG} ]]; then
    oCI_ORG="istresearch"
  fi
  oCI_PROJECT=$1
  BRANCH=$2
  BUILD_PARAMS=$3
  PARAMS="\"branch\":\"${BRANCH}\""
  #NOTE1: v1.1 api does NOT handle "build_parameters" (yet, been years tho)
  API_URL="https://circleci.com/api/v1.1/project/github/${oCI_ORG}/${oCI_PROJECT}/build?circle-token=${oCI_API_TOKEN}"
  if [[ -n $BUILD_PARAMS ]]; then
    PARAMS="${PARAMS},\"build_parameters\":${BUILD_PARAMS}"
    #NOTE: v1 does NOT handle workflows and therefore no context, YOU HAVE BEEN WARNED!
    API_URL="https://circleci.com/api/v1/project/${oCI_ORG}/${oCI_PROJECT}/tree/${BRANCH}?circle-token=${oCI_API_TOKEN}"
  fi
  PrintPaddedTextRight "Trigger Build" "${oCI_PROJECT}/${BRANCH}" ${COLOR_MSG_INFO}
  export BUILD_INFO=$(curl -X POST -H "Content-Type: application/json" -d "{${PARAMS}}" $API_URL)
  TRIGGERED_URL=$(echo ${BUILD_INFO} | grep -Po 'build_url" : "\K.+?"')
  # the trailing " will need to be stripped still from ^
  if [[ -z ${TRIGGERED_URL} ]]; then
    # leave a trailing space that will be stripped at last echo statement
    TRIGGERED_URL="https://circleci.com/gh/${oCI_ORG}/${oCI_PROJECT}/tree/${BRANCH} "
  fi
  echo -e "Follow the progress of the build on: [${COLOR_MSG_INFO}${TRIGGERED_URL%?}${COLOR_NONE}]"
}

####################
# Verify a specific tagged DockerHub image exists.
# DockerHub introduced a (bug?) requirement to sleep 1 second between login and whatever.
# e.g.: if DockerImageTagExists istresearch/joka ${JOKA_TAG}; then
# @param string $1 - DockerHub image name.
# @param string $2 - the image tag.
# @ENV DOCKER_USER - the circleci DockerHub username
# @ENV DOCKER_PASS - the circleci DockerHub password
function DockerImageTagExists
{
  TOKEN=$(curl -s -H "Content-Type: application/json" -X POST -d '{"username": "'${DOCKER_USER}'", "password": "'${DOCKER_PASS}'"}' https://hub.docker.com/v2/users/login/ | jq -r .token)
  sleep 1
  EXISTS=$(curl -s -H "Authorization: JWT ${TOKEN}" https://hub.docker.com/v2/repositories/$1/tags/?page_size=10000 | jq -r "[.results | .[] | .name == \"$2\"] | any")
  test $EXISTS = true
}

####################
# Create a new commit and push it up to GitHub.
# @param string $1 - the branch name to which we are committing.
# @param string $2 - the commit message.
function PushNewGitCommit
{
  git config branch.$1.remote origin
  git config branch.$1.merge refs/heads/branch
  git config user.email "circleci@istresearch.com"
  git config user.name "circleci"
  git commit --allow-empty -m "$2" .
  git push origin $1
}

####################
# Create a new comment on a GitHub PR.
# @param string $1 - the comment message.
# @return string Returns the results of the curl command.
# @ENV GITHUB_API_TOKEN - the GitHub auth token to use.
function CreateGitPRComment
{
  oCI_ORG=$CIRCLE_PROJECT_USERNAME
  oCI_PROJECT=$CIRCLE_PROJECT_REPONAME
  PR_NUMBER=${CIRCLE_PULL_REQUEST##*/}
  PR_COMMENT=$1
  if [[ -n "$PR_NUMBER" && -n "$PR_COMMENT" && -n "${GITHUB_API_TOKEN}" ]]; then
    echo $(curl -s -X POST -H "Content-Type: application/json" -H "Authorization: token ${GITHUB_API_TOKEN}" \
        -d "{\"body\":\"${PR_COMMENT}\"}" \
        "https://api.github.com/repos/${oCI_ORG}/${oCI_PROJECT}/issues/${PR_NUMBER}/comments")
    PrintPaddedTextRight "PR comment" "CREATED" ${COLOR_MSG_INFO}
  elif [[ -z "${GITHUB_API_TOKEN}" ]]; then
    PrintPaddedTextRight "GitHub API Token" "MISSING" ${COLOR_MSG_WARNING}
    PrintPaddedTextRight "PR comment" "SKIPPED" ${COLOR_MSG_INFO}
  elif [[ -z "$PR_COMMENT" ]]; then
    PrintPaddedTextRight "PR comment is blank" "SKIPPED" ${COLOR_MSG_INFO}
  else
    PrintPaddedTextRight "PR comment on non-PR" "SKIPPED" ${COLOR_MSG_INFO}
  fi
}

####################
# Round and return the given string so last char is either 0 or 5 if numeric.
# @param string $1 - the timestamp string without timezone info to round to 0 or 5.
# @RETURNS the given string rounded to 0 or 5.
function RoundTimestampTo5Min()
{
  TIMESTAMP=$1
  case $TIMESTAMP in
    *[1234]) TIMESTAMP=${TIMESTAMP%?}0;;
    *[6789]) TIMESTAMP=${TIMESTAMP%?}5;;
  esac
  echo $TIMESTAMP
}

####################
# Get now as a 5-minute round-down ISO-8601 string.
# @returns the current 0 or 5 min floored datetime string.
function GetNowToLast5MinMark()
{
  echo $(RoundTimestampTo5Min $(date "+%Y%m%dT%H%M"))
}

####################
# Generate two timestamp-based window Artifact folder names for CircleCI build artifacts.
# Used to "pass information" to a triggered repo build. Hack workaround for
# lack of CircleCI feature.
# @ENV ART_FOLDER1 - timestamp-based window prefix
# @ENV ART_FOLDER2 - the next timestamp-based window prefix
function CreateBuildArtifactTimestampFolders
{
  export ART_FOLDER1=$(GetXRoundedToNearestY $(date "+%s") 100)
  export ART_FOLDER2=$(( ${ART_FOLDER1} + 100 ))
}

####################
# Due to limitations of CircleCI's API, we cannot pass ENV vars into a triggered workflow.
# Due to limitations of the config.yml on ENV var processing, we have to use static paths.
# Thanks to these limitations, we have to use a static Artifact base path that contains
# all our variations we desire with ENV vars. Theory, in order to trigger another repo
# built that relies on info we pass to it, we use time as a factor rounding to nearest
# 100 seconds. We use 2 such bins by adding 100 to the current rounded timestamp so that
# when the triggered repo imports the Artifacts, if the time delay would have bumped the
# rounding to the next bin, it will still have the data we desire. 100 seconds is short
# enough time window to not interfere with frequents builds on same day and long enough
# to span a trigger event.
# @param string $1 - the data to store
# @param string $2 - the filename in which to store the data.
function ExportAsArtifact
{
  if [[ -z ${ART_FOLDER1} || -z ${ART_FOLDER2} ]]; then
    CreateBuildArtifactTimestampFolders
  fi
  ART_PATH1="${ARTIFACT_PATH}/tmp/${ART_FOLDER1}"
  mkdir -p "${ART_PATH1}"
  ART_PATH2="${ARTIFACT_PATH}/tmp/${ART_FOLDER2}"
  mkdir -p "${ART_PATH2}"
  echo "$1" >> "${ART_PATH1}/$2"
  echo "$1" >> "${ART_PATH2}/$2"
}

####################
# Import an artifact created by ExportAsArtifact from a different repo build process.
# See ExportAsArtifact for details.
# @param string $1 - the "org/project" whose artifacts we desire, e.g. "istresearch/PULSE"
# @param string $2 - the filename in which to retrieve the data.
# @return string Returns the file contents as a string.
function ImportFromArtifact
{
  REPO_SLUG=$1 #github <name|org>/<project> slug
  FILE_NAME=$2
  if [[ -z ${ART_FOLDER1} || -z ${ART_FOLDER2} ]]; then
    CreateBuildArtifactTimestampFolders
  fi
  if [[ -z ${ART_LATEST} ]]; then
    export ART_LATEST=$(GetBuildArtifactsForProject $REPO_SLUG)
  fi
  if [[ -z ${ART_URLS} ]]; then
    export ART_URLS=( $(echo ${ART_LATEST} | jq -r '.[] | .url') )
  fi
  # EXAMPLE ART_URLS array contents:
  # https://1779-15237156-gh.circle-artifacts.com/0/artifacts/tmp/1586534600/version_api.txt
  # https://1779-15237156-gh.circle-artifacts.com/0/artifacts/tmp/1586534600/version_str.txt
  # https://1779-15237156-gh.circle-artifacts.com/0/artifacts/tmp/1586534600/version_tag.txt
  # https://1779-15237156-gh.circle-artifacts.com/0/artifacts/tmp/1586534700/version_api.txt
  # https://1779-15237156-gh.circle-artifacts.com/0/artifacts/tmp/1586534700/version_str.txt
  # https://1779-15237156-gh.circle-artifacts.com/0/artifacts/tmp/1586534700/version_tag.txt
  for url in "${ART_URLS[@]}"; do
    # only check ART_FOLDER1 as the ART_FOLDER2 is computed in case the Import time
    #   happens to be very close to the rounding border, in which case ART_FOLDER1 would
    #   equal Export's ART_FOLDER2.
    if [[ $url == */tmp/${ART_FOLDER1}/${FILE_NAME} ]]; then
      echo $(curl -L --silent $url"?circle-token=${oCI_API_TOKEN}")
    fi
  done
}

####################
# Retrieve CircleCI build artifacts.
# @param string $1 - the "org/project" whose artifacts we desire, e.g. "istresearch/PULSE"
# @return Returns the JSON result of the latest artifacts endpoint.
function GetBuildArtifactsForProject
{
  API_URL=https://circleci.com/api/v1.1/project/github/$1/latest/artifacts
  echo $(curl -L --silent $API_URL"?circle-token=${oCI_API_TOKEN}")
}

####################
# Add an ENV var to a particular project.
# @param string $1 - the "org/project" we desire to poke, e.g. "istresearch/Pulse-UI"
# @param string $2 - ENV var name
# @param string $3 - ENV var value
function AddEnvVarToProject
{
  API_URL=https://circleci.com/api/v1.1/project/github/$1/envvar
  echo $(curl --silent -X POST --header "Content-Type: application/json" -d '{"name":"'$2'","value":"'$3'"}' \
      $API_URL"?circle-token=${oCI_API_TOKEN}")
}

####################
# Remove a single ENV var for a particular project.
# @param string $1 - the "org/project" we desire to poke, e.g. "istresearch/Pulse-UI"
# @param string $2 - ENV var name.
function DelEnvVarToProject
{
  API_URL=https://circleci.com/api/v1.1/project/github/$1/envvar/$2
  echo $(curl --silent -X DELETE $API_URL"?circle-token=${oCI_API_TOKEN}")
}

####################
# Given a file, return its timestamp formatted to the minute as IST-8601 without timezone.
# @param string $1 - the file.
# @RETURNS the timestamp formatted like: "yyyymmddThhmm"
function GetFileTimestampToTheMinute()
{
  echo $(date -r $1 "+%Y%m%dT%H%M")
}

####################
# Get the most recent file from set of given files/file-patterns.
# @param string $1..$n - the file or file pattern of files to sort and get most recent name.
# @RETURNS the name of the most recent file specified in its arg list.
function GetMostRecentFile()
{
  echo $(ls -rct $@ | tail -1)
}

####################
# Get the MD5 hash of the set of passed in files.
# @param string $1..$n - the files to get their concatinated MD5 hash.
# @RETURNS the MD5 hash of the concatinated file list.
function CalcFileArgsMD5()
{
  #os-x cmd is md5, alpine is md5sum
  if command -v md5 &> /dev/null; then
    echo `cat $@ | md5 -q`
  else
    echo `cat $@ | md5sum - | awk '{ print $1 }'`
  fi
}
