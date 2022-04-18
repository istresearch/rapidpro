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

####################
# Concatenate the args with a dot, "."; e.g. $(buildVersionNum 3 1 4)="3.1.4".
function buildVersionNum
{
  VERSION_NUM=""
  for var in "$@"; do
    if [[ -n $var ]]; then
      VERSION_NUM="${VERSION_NUM}.$var"
    fi
  done
  echo "${VERSION_NUM:1}"
}

####################
# Timestamp based version num tructaed to 10 min mark so it stays within
# 2 billion INT range until year 2100. 80 years should be sufficient scale.
function createVersionNumFrom10minTs
{
    VER_BUILD=$(date +%H%M)
    # Round to nearest 10 minutes, else resulting number is near MAX_INT on Android.
    echo $(buildVersionNum "$(date +%y)" "$(date +%m)" "$(date +%d)" "${VER_BUILD:0:3}")
}

####################
# Parse the branch name or the tag to determine version number, if possible.
# usage: VERSION_NUM=$(parseVersionNumFromBranchNameOrTag)
function parseVersionNumFromBranchNameOrTag
{
  if [[ ${BRANCH_NAME} =~ (release|staging)-v([[:digit:]]+)\.([[:digit:]]+)\.([[:digit:]]+)\.{0,1}([[:digit:]]*)$ ]] || \
     [[ ${CIRCLE_TAG} =~ (v|beta)([[:digit:]]+)\.([[:digit:]]+)\.([[:digit:]]+)\.{0,1}([[:digit:]]*)$ ]]
  then
    echo $(buildVersionNum "${BASH_REMATCH[2]}" "${BASH_REMATCH[3]}" "${BASH_REMATCH[4]}" "${BASH_REMATCH[5]}")
  fi
}

####################
# Parse the branch name or the tag to determine version kind.
# Possible values are 'dev' | 'beta' | 'gold'.
# usage: VERSION_KIND=$(parseVersionKindFromBranchNameOrTag)
function parseVersionKindFromBranchNameOrTag
{
  VER_KIND="dev"
  if [[ ${BRANCH_NAME} =~ (release|staging)-v([[:digit:]]\.)+ ]]; then
    local theVerKindHint=
    if [[ -z ${BASH_REMATCH[1]} ]]; then
      if [[ ${CIRCLE_TAG} =~ (v|beta)([[:digit:]]\.)+ ]]; then
        theVerKindHint=${BASH_REMATCH[1]};
      fi
    else
      theVerKindHint=${BASH_REMATCH[1]};
    fi
    if [[ $theVerKindHint == "release" || $theVerKindHint == "v" ]]; then
      VER_KIND="gold"
    elif [[ $theVerKindHint == "staging" || $theVerKindHint == "beta" ]]; then
      VER_KIND="beta"
    fi
  fi
  echo $VER_KIND
}

####################
# Read version info or parse it from branch/tag to determine version info.
# usage: VERSION_STRING=$(parseVersionInfo)
# @ENV VERSION_NUM - sets this ENV, e.g. 21.02.29.152 or 3.1.4
# @ENV VERSION_INT - sets this ENV as datetime to nearest 10min, e.g. 210229152
# @ENV VERSION_KIND - sets this ENV, e.g. beta
# @ENV VERSION_STR - sets this ENV, e.g. 3.1.4-beta
function parseVersionInfo
{
  VER_NUM=$(createVersionNumFrom10minTs)
  VER_INT="${VER_NUM//.}"

  if [[ ! -d "${WORKSPACE}/info" ]]; then
    mkdir -p "${WORKSPACE}/info"
  fi

  VER_NUM_FILE="${WORKSPACE}/info/version_num.txt"
  if [[ -f "$VER_NUM_FILE" ]]; then
    export VERSION_NUM=$(cat "$VER_NUM_FILE")
  else
    export VERSION_NUM=$(parseVersionNumFromBranchNameOrTag)
    if [[ -z ${VERSION_NUM} ]]; then
      export VERSION_NUM=${VER_NUM}
    fi
    echo "${VERSION_NUM}" > "$VER_NUM_FILE"
  fi

  VER_INT_FILE="${WORKSPACE}/info/version_int.txt"
  if [[ -f "$VER_INT_FILE" ]]; then
    export VERSION_INT=$(cat "$VER_INT_FILE")
  else
    export VERSION_INT=${VER_INT}
    echo "${VERSION_INT}" > "$VER_INT_FILE"
  fi

  VER_KIND_FILE="${WORKSPACE}/info/version_kind.txt"
  if [[ -f "$VER_KIND_FILE" ]]; then
    export VERSION_KIND=$(cat "$VER_KIND_FILE")
  else
    export VERSION_KIND=$(parseVersionKindFromBranchNameOrTag)
    echo "${VERSION_KIND}" > "$VER_KIND_FILE"
  fi

  VER_STR_FILE="${WORKSPACE}/info/version_str.txt"
  if [[ -f "$VER_STR_FILE" ]]; then
    export VERSION_STR=$(cat "$VER_STR_FILE")
  else
    VER_SUFFIX=""
    if [[ ${VERSION_KIND} != "gold" ]]; then
      VER_SUFFIX="-${VERSION_KIND}"
    fi
    export VERSION_STR="${VERSION_NUM}${VER_SUFFIX}"
    echo "${VERSION_STR}" > "$VER_STR_FILE"
  fi

  echo "${VERSION_STR}"
}

####################
# Retrieve the read/parsed version string.
# usage: VERSION_STRING=`getVersionStr`
# may also set these ENV vars:
# @ENV VERSION_NUM - sets this ENV after parsing version number.
# @ENV VERSION_INT - sents this ENV to YYMMDDHHM integer.
# @ENV VERSION_KIND - sets this ENV after parsing version kind.
# @ENV VERSION_STR - sets this ENV after parsing version info.
function getVersionStr
{
  if [[ -z ${VERSION_STR} ]]; then
    parseVersionInfo
  else
    echo "${VERSION_STR}"
  fi
}

####################
# Upload a given file to a path in repo.istresearch.com.
# @param string $1 - the file to upload.
# @param string $2 - the filepath of the destination.
# @ENV REPO_HOST - the repo host to use; default used in case it is empty.
function setupRepoSSH
{
  if [[ -z "${REPO_HOST}" ]]; then
    REPO_HOST=infra.dev.istresearch.com
  fi
  REPO_SSH_USER="$(id -u -n)"
  export SCP_SSH="${REPO_SSH_USER}@${REPO_HOST}"
  #export SCP_OPT="ProxyJump $ANSIBLE_EXECUTOR_USER@$ANSIBLE_EXECUTOR_HOST"
  if [[ ! -d ~/.ssh ]]; then
    mkdir ~/.ssh
  fi
  ssh-keyscan -H $ANSIBLE_EXECUTOR_HOST >> ~/.ssh/known_hosts
  ssh $ANSIBLE_EXECUTOR_USER@$ANSIBLE_EXECUTOR_HOST "ssh-keyscan -H ${REPO_HOST}" >> ~/.ssh/known_hosts
  chmod 600 ~/.ssh/known_hosts
  export SCP_PROGRESS_FILE=/tmp/scp-progress-${AUTOBUILD_DATETIME_STAMP}.log
}

####################
# Upload a given file to a path in repo.istresearch.com.
# @param string $1 - the file to upload.
# @param string $2 - the filepath of the destination.
# @param 0 or 1 $3 - boolean: 1 means DO NOT overwrite destination if already exists.
function uploadFileToRepo
{
  if [[ -z ${SCP_SSH} ]]; then
    setupRepoSSH
  fi
  LOCAL_SRC_FILE="$1"
  REMOTE_DST_FILE="$2"
  if [ -f "${LOCAL_SRC_FILE}" ]; then
    if [[ "$3" == "1" && -n $(SpotCheckRemoteFile ${SCP_SSH} ${REMOTE_DST_FILE}) ]]; then
      PrintPaddedTextRight "${REMOTE_DST_FILE} already uploaded" "SKIPPED" "1;31"
      return
    fi
    local src=$(basename "${LOCAL_SRC_FILE}")
    local dst=$(basename "${REMOTE_DST_FILE}")
    local x="${src} => ${dst}"
    echo "Uploading ${x}..."
    trap "rm ${SCP_PROGRESS_FILE}" EXIT
    scp -o "ProxyJump $ANSIBLE_EXECUTOR_USER@$ANSIBLE_EXECUTOR_HOST" "${LOCAL_SRC_FILE}" "${SCP_SSH}:${REMOTE_DST_FILE}" >> "${SCP_PROGRESS_FILE}"
    if [ $? -eq 0 ]; then
      PrintPaddedTextRight "${flavor} file upload [${x}]" "OK" ${COLOR_MSG_INFO}
    else
      PrintPaddedTextRight "${flavor} file upload [${x}]" "FAILED" ${COLOR_MSG_WARNING}
      exit 2
    fi
  else
    echo -e "${COLOR_MSG_WARNING}Local file ${LOCAL_SRC_FILE} not found.${COLOR_NONE}"
    exit 1
  fi
}

####################
# Multi-architecture Docker images require some bleeding edge software, buildx.
# Use this function to install Docker `buildx`.
# @see https://docs.docker.com/engine/install/ubuntu/
# Used with machine image: ubuntu-2004:202111-02 (Ubuntu 20.04, revision: Nov 02, 2021)
function multiArch_installBuildx()
{
  # Uninstall older versions of Docker, ok if it reports none are installed.
  sudo apt-get remove docker docker-engine docker.io containerd runc;
  # install using repository
  sudo apt-get update && sudo apt-get install \
    ca-certificates \
    curl \
    gnupg \
    lsb-release;
  # add Docker's official GPG key
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg;
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
    $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null;
  # install docker engine
  sudo apt-get update && sudo apt-get install docker-ce docker-ce-cli containerd.io;
  # test engine installation
  sudo docker run hello-world;
}

####################
# Multi-architecture Docker images require some bleeding edge software, buildx.
# Use this function to install arm64 architecture.
# @see https://docs.docker.com/engine/install/ubuntu/
# Used with machine image: ubuntu-2004:202111-02 (Ubuntu 20.04, revision: Nov 02, 2021)
# @ENV USER - the circleci user that executes commands.
function multiArch_addArm64Arch()
{
  sudo apt-get update && sudo apt-get install \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg-agent \
    software-properties-common;
  sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
  sudo apt-get update && sudo apt-get install docker-ce docker-ce-cli containerd.io;
  # so we don't have to use sudo
  sudo groupadd docker && sudo usermod -aG docker $USER && newgrp docker;
  # emulation deps
  sudo apt-get install binfmt-support qemu-user-static;
  # test engine installation again to show what arch it supports
  sudo docker run hello-world;
}

####################
# Multi-architecture Docker images require some bleeding edge software, buildx.
# Use this function to create and use a new builder context.
# @see https://docs.docker.com/engine/install/ubuntu/
# Used with machine image: ubuntu-2004:202111-02 (Ubuntu 20.04, revision: Nov 02, 2021)
# @param string $1 - (OPTIONAL) the name of the context to use (defaults to 'mabuilder').
function multiArch_createBuilderContext()
{
  DOCKER_CONTEXT=${1:-mabuilder};
  docker context create "${DOCKER_CONTEXT}";
  docker buildx create "${DOCKER_CONTEXT}" --use;
}

####################
# Use this function to build multi-architecture container images and push them to DockerHub.
# @param string $1 - image name to use (w/o the tag); if empty, it is constructed from CI vars.
# @param string $2 - image tag to use; if empty, it will use getVersionStr()
# @param string $3 - docker build file to use; if empty, "docker/Dockerfile" is used.
# @param string $4…- (OPTIONAL) extra docker build args, e.g. --build-arg "APK_URI=${APK_URI}"
function multiArch_buildImages()
{
  IMG_NAME="$1"
  if [[ -z ${IMG_NAME} ]]; then
    IMG_NAME=${CIRCLE_PROJECT_USERNAME}/${CIRCLE_PROJECT_REPONAME}
  fi
  IMG_TAG="$2"
  if [[ -z $IMG_TAG ]]; then
    IMG_TAG=getVersionStr
  fi
  DOCKER_FILE_TO_USE="${3:-docker/Dockerfile}"
  set -x
  docker buildx build --progress=plain \
    --platform linux/amd64,linux/arm64 \
    -t "$IMG_NAME:$IMG_TAG" \
    -f "$DOCKER_FILE_TO_USE" \
    "$@" \
    --push .
  if [ $? -eq 0 ]; then
    PrintPaddedTextRight "$IMG_NAME:$IMG_TAG build and upload" "OK" "${COLOR_MSG_INFO}"
  else
    PrintPaddedTextRight "$IMG_NAME:$IMG_TAG build and upload" "FAILED" "${COLOR_MSG_WARNING}"
    exit 2
  fi
}

####################
# Use this function to build a standard "docker build" image and push it to DockerHub.
# @param string $1 - image name to use (w/o the tag); if empty, it is constructed from CI vars.
# @param string $2 - image tag to use; if empty, it will use getVersionStr()
# @param string $3 - docker build file to use; if empty, "docker/Dockerfile" is used.
# @param string $4…- (OPTIONAL) extra docker build args, e.g. --build-arg "APK_URI=${APK_URI}"
function buildImage()
{
  IMG_NAME="$1"
  if [[ -z ${IMG_NAME} ]]; then
    IMG_NAME=${CIRCLE_PROJECT_USERNAME}/${CIRCLE_PROJECT_REPONAME}
  fi
  IMG_TAG="$2"
  if [[ -z $IMG_TAG ]]; then
    IMG_TAG=getVersionStr
  fi
  DOCKER_FILE_TO_USE="${3:-docker/Dockerfile}"

  docker build --progress=plain \
    -t "$IMG_NAME:$IMG_TAG" \
    -f "$DOCKER_FILE_TO_USE" \
    "$@" \
    .
  if [ $? -eq 0 ]; then
    PrintPaddedTextRight "$IMG_NAME:$IMG_TAG build" "OK" "${COLOR_MSG_INFO}"
  else
    PrintPaddedTextRight "$IMG_NAME:$IMG_TAG build" "FAILED" "${COLOR_MSG_WARNING}"
    exit 2
  fi
  docker push "${IMG_NAME}:${IMG_TAG}"
}
