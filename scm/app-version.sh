#!/bin/bash
##########################################################################################
# Ensure a release build version strings, numbers, and tokens all match the branch name.
#
# To prevent a commit from triggering a build, add "[skip ci]" to the commit message.
##########################################################################################

export SCRIPT_PATH=$(dirname "$0")
source "${SCRIPT_PATH}/utils.sh"
source "${SCRIPT_PATH}/utils-angularjs.sh"

###############################################################################
# MAIN SCRIPT BODY
###############################################################################

# start off in our repo directory
cd ${REPO_PATH}

PrintPaddedTextRight "BRANCH_NAME" "${BRANCH_NAME}" ${COLOR_MSG_INFO}

if [[ -z $BUILD_TRIGGERED_FOR ]]; then
  CreateBuildArtifactTimestampFolders
else
  export ART_FOLDER1=$BUILD_TRIGGERED_FOR
fi
echo "Checking ENV vars and artifacts in PULSE for [${ART_FOLDER1}]."
export VERSION_STR=$(ImportFromArtifact "istresearch/PULSE" "version_str.txt")
export VERSION_API=$(ImportFromArtifact "istresearch/PULSE" "version_api.txt")
export JOKA_TAG=$(ImportFromArtifact "istresearch/PULSE" "version_tag.txt")

if [[ -z $VERSION_STR ]]; then
  echo "No artifacts for [${ART_FOLDER1}] found, generating our own tags."
  #VER_KIND = 'dev' | 'beta' | 'gold'
  VER_KIND="gold"
  VER_SUFFIX=""

  if [[ ${BRANCH_NAME} =~ (release|staging)-v([[:digit:]]+)\.([[:digit:]]+)\.([[:digit:]]+)$ ]] || \
     [[ ${BRANCH_NAME} =~ (release|staging)-v([[:digit:]]+)\.([[:digit:]]+)\.([[:digit:]]+)\.([[:digit:]]+)$ ]] || \
     [[ ${CIRCLE_TAG} =~ (v)([[:digit:]]+)\.([[:digit:]]+)\.([[:digit:]]+)$ ]] || \
     [[ ${CIRCLE_TAG} =~ (v)([[:digit:]]+)\.([[:digit:]]+)\.([[:digit:]]+)\.([[:digit:]]+)$ ]]
  then
    if [[ BASH_REMATCH[1] == "staging" ]]; then
      VER_KIND="beta"
      VER_SUFFIX="-beta"
    fi
    ############################################################
    # "release-v6.9.0" or "release-v6.9.0.1"
    ############################################################
    VER_MAJOR="${BASH_REMATCH[2]}"
    VER_MINOR="${BASH_REMATCH[3]}"
    VER_MAINT="${BASH_REMATCH[4]}"
    VER_BUILD="${BASH_REMATCH[5]}"
    # update the branch with our calculated version info
    SHOULD_COMMIT=1
  else
    # non-release branches get a suffix in its label and versioning based on minute
    VER_MAJOR=$(date +%y)
    VER_MINOR=$(date +%m)
    VER_MAINT=$(date +%d)
    VER_BUILD=$(date +%H%M)
    VER_KIND="dev"
    VER_SUFFIX="-dev"
    # DO NOT update the branch with our calculated version info
    SHOULD_COMMIT=0
  fi
  # construct the server version string
  SERVER_VERSION="${VER_MAJOR}"
  if [[ -n ${VER_MINOR} ]]; then
    SERVER_VERSION="${SERVER_VERSION}.${VER_MINOR}"
  fi
  if [[ -n ${VER_MAINT} ]]; then
    SERVER_VERSION="${SERVER_VERSION}.${VER_MAINT}"
  fi
  if [[ -n ${VER_BUILD} ]]; then
    SERVER_VERSION="${SERVER_VERSION}.${VER_BUILD}"
  fi
  SERVER_VERSION="${SERVER_VERSION}${VER_SUFFIX}"
  # perform this check after setting the version string as we don't want to show "x.y.z.0"
  if [[ -z ${VER_BUILD} ]]; then
    # used to generate the API token to mean "no hotfix version yet"
    VER_BUILD="0"
  fi
else
  PrintPaddedTextRight "Received Version String" "$VERSION_STR" ${COLOR_MSG_INFO}
  SERVER_VERSION=$VERSION_STR
  if [[ $SERVER_VERSION == *dev ]]; then
    VER_KIND="dev"
    # DO NOT update the branch with our calculated version info
    SHOULD_COMMIT=0
  else
    if [[ $SERVER_VERSION == *beta ]]; then
      VER_KIND="beta"
    else
      VER_KIND="gold"
    fi
    # update the branch with our calculated version info
    SHOULD_COMMIT=1
  fi
fi

if [[ -z $VERSION_API ]]; then
  API_TOKEN=$(date +%y)$(printf "%02d" "${VER_MAINT#0}")$(printf "%02d" "${VER_BUILD#0}")
else
  PrintPaddedTextRight "Received API Token" "$VERSION_API" ${COLOR_MSG_INFO}
  API_TOKEN=$VERSION_API
fi

PrintPaddedTextRight "UPDATE UI VERSION" "${SERVER_VERSION}" ${COLOR_MSG_INFO}

# commit defaults to "do not commit"
PUSH_COMMIT=0
$(VerifyUIProjectVersion "${REPO_PATH}" ${SERVER_VERSION} ${API_TOKEN} ${API_TOKEN})
r=$?
if [[ $r -ne 0 ]]; then
  FailUIProjectVersion "${REPO_PATH}" $r
  # if file found, but version incorrect, update the version info
  if [[ $r -ne 4 ]]; then
    PUSH_COMMIT=$SHOULD_COMMIT
    PrintPaddedTextRight "bumping version info" "${SERVER_VERSION}" ${COLOR_MSG_INFO}
    # version info needs updating which will trigger a CircleCI build of the UI
    BumpUIProjectVersion "${REPO_PATH}" ${SERVER_VERSION} ${API_TOKEN} ${API_TOKEN}
    r=0
  fi
fi

if [[ $PUSH_COMMIT -eq 1 ]]; then
    COMMIT_MSG="Advanced version info to Portal: ${SERVER_VERSION}"
    # To prevent a commit from triggering a new build, add "[skip ci]" to the commit message.
    COMMIT_MSG="${COMMIT_MSG} [skip ci]"
    PushNewGitCommit ${BRANCH_NAME} "${COMMIT_MSG}"
fi
if [[ $r -eq 0 ]]; then
  PrintPaddedTextRight "Version Information Verified" "${SERVER_VERSION}" ${COLOR_MSG_INFO}
  # stuff we need in later steps
  echo "${SERVER_VERSION}" >> "${SCRIPT_PATH}/server_version.txt"
  echo "${API_TOKEN}" >> "${SCRIPT_PATH}/api_token.txt"
  if [[ ${BRANCH_NAME} == "develop" ]]; then
    VERSION_TAG="ci-develop"
  else
    VERSION_TAG=${SERVER_VERSION}
  fi
  echo "${VERSION_TAG}" >> "${SCRIPT_PATH}/version_tag.txt"
  if [[ -z ${JOKA_TAG} ]]; then
    JOKA_TAG=${SERVER_VERSION}
  else
    PrintPaddedTextRight "Received Joka Tag" "$JOKA_TAG" ${COLOR_MSG_INFO}
  fi
else
  exit $r
fi

# ensure the Joka DockerHub exists, else fail
FAIL_MSG="Joka container tag ${JOKA_TAG} & 'ci-develop'"
if DockerImageTagExists istresearch/joka ${JOKA_TAG}; then
  echo "${JOKA_TAG}" >> "${SCRIPT_PATH}/joka_tag.txt"
  PrintPaddedTextRight "From Joka container" "${JOKA_TAG}" ${COLOR_MSG_INFO}
else
  JOKA_TAG="ci-develop"
  if DockerImageTagExists istresearch/joka ${JOKA_TAG}; then
    echo "${JOKA_TAG}" >> "${SCRIPT_PATH}/joka_tag.txt"
    PrintPaddedTextRight "From Joka container" "${JOKA_TAG}" ${COLOR_MSG_INFO}
  else
    PrintPaddedTextRight "${FAIL_MSG}" "NOT FOUND" ${COLOR_MSG_WARNING}
    exit 5
  fi
fi
