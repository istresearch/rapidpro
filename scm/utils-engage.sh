#!/bin/bash

#####################
# Utilities that are helpful for an SCM script that builds a Node lib image.
#####################

if [ "$0" = "$BASH_SOURCE" ]; then
    echo "Error: Script must be sourced"
    exit 1
fi

if [[ -z "${UTILS_PATH}" ]]; then
  UTILS_PATH=scm
fi
source "${UTILS_PATH}/utils.sh"

DEFAULT_IMAGE_NAME="${CIRCLE_PROJECT_USERNAME}/p4-engage"


####################
# Get the file containing the image tag  for stage image specified by arg.
# @param string $1 - the stage image base name.
function GetImgStageFile()
{
  IMG_STAGE=$1
  TAG_FILE="${WORKSPACE}/info/${IMG_STAGE}_tag.txt"
  if [ -f "${TAG_FILE}" ]; then
    echo "${TAG_FILE}"
  else
    echo "${UTILS_PATH}/${IMG_STAGE}_tag.txt"
  fi
}

####################
# Get the image tag for stage image specified by arg.
# @param string $1 - the stage image base name.
function GetImgStageTag()
{
  IMG_STAGE_FILE=$(GetImgStageFile $1)
  if [[ ! -f "${IMG_STAGE_FILE}" ]]; then
    echo "Error: ${IMG_STAGE_FILE} not found."
    exit 2
  fi
  echo "`cat ${IMG_STAGE_FILE}`"
}

####################
# Determine the image tag for Python3-based image best used for later stages.
# Ensure the docker image tagged with the special tag exists; build if needed.
function EnsureBaseImageExists()
{
  IMAGE_NAME="${DEFAULT_IMAGE_NAME}"
  IMG_STAGE="base"
  DOCKERFILE2USE="docker/dfstage-${IMG_STAGE}.dockerfile"
  IMAGE_TAG_HASH=$(CalcFileArgsMD5 "${DOCKERFILE2USE}")
  IMAGE_TAG="${IMG_STAGE}-${IMAGE_TAG_HASH}"
  echo "${IMAGE_TAG}" > "${WORKSPACE}/info/${IMG_STAGE}_tag.txt"
  if ! DockerImageTagExists "${IMAGE_NAME}" "${IMAGE_TAG}"; then
    if [[ -z $(multiArch_isBuildx) ]]; then
      # prep for multi-arch building
      multiArch_installBuildx
      multiArch_addArm64Arch
      multiArch_createBuilderContext
    fi
    echo "Building Docker container ${IMAGE_NAME}:${IMAGE_TAG}…"
    multiArch_buildImages "${IMAGE_NAME}" "${IMAGE_TAG}" "${DOCKERFILE2USE}"
    "${UTILS_PATH}/pr-comment.sh" "Base Image built: ${IMAGE_NAME}:${IMAGE_TAG}"
  fi
  PrintPaddedTextRight "Using Base Image Tag" "${IMAGE_TAG}" "${COLOR_MSG_INFO}"
}

####################
# Determine the image tag for Python Libs image based on its requirements file(s).
# Ensure the docker image tagged with the special tag exists; build if needed.
# @param string $1 - the image stage string to use, "pylibs" if empty.
function EnsurePyLibsImageExists()
{
  IMAGE_NAME="${DEFAULT_IMAGE_NAME}"
  IMG_STAGE=${1:-"pylibs"}
  DOCKERFILE2USE="docker/dfstage-${IMG_STAGE%-*}.dockerfile"
  IMAGE_TAG_HASH=$(CalcFileArgsMD5 "${DOCKERFILE2USE}" "$(GetImgStageFile "base")" "poetry.lock" "pyproject.toml" "package-lock.json" "package.json")
  IMAGE_TAG="${IMG_STAGE}-${IMAGE_TAG_HASH}"
  echo "${IMAGE_TAG}" > "${WORKSPACE}/info/${IMG_STAGE}_tag.txt"
  if ! DockerImageTagExists "${IMAGE_NAME}" "${IMAGE_TAG}"; then
    FROM_STAGE_TAG=$(GetImgStageTag "base")
    PrintPaddedTextRight "  Using Base Tag" "${FROM_STAGE_TAG}" "${COLOR_MSG_INFO}"

    echo "Building Docker container ${IMAGE_NAME}:${IMAGE_TAG}…"
    buildImage "${IMAGE_NAME}" "${IMAGE_TAG}"  "${DOCKERFILE2USE}" \
      --build-arg "FROM_STAGE=${IMAGE_NAME}:${FROM_STAGE_TAG}" \
      --build-arg "ARCH=${IMG_STAGE##*-}/"

    "${UTILS_PATH}/pr-comment.sh" "Python/NPM Libs Image built: ${IMAGE_NAME}:${IMAGE_TAG}"
  fi
  PrintPaddedTextRight "Using Python/NPM Libs Image Tag" "${IMAGE_TAG}" "${COLOR_MSG_INFO}"
}

####################
# Determine the image tag for Python Libs image based on its requirements file(s).
# Ensure the docker image tagged with the special tag exists; build if needed.
function EnsurePyLibsManifestExists()
{
  IMAGE_NAME="${DEFAULT_IMAGE_NAME}"
  IMG_STAGE="pylibs"
  DOCKERFILE2USE="docker/dfstage-${IMG_STAGE}.dockerfile"
  IMAGE_TAG_HASH=$(CalcFileArgsMD5 "${DOCKERFILE2USE}" "$(GetImgStageFile "base")" "poetry.lock" "pyproject.toml" "package-lock.json" "package.json")
  IMAGE_TAG="${IMG_STAGE}-${IMAGE_TAG_HASH}"
  echo "${IMAGE_TAG}" > "${WORKSPACE}/info/${IMG_STAGE}_tag.txt"
  if ! DockerImageTagExists "${IMAGE_NAME}" "${IMAGE_TAG}"; then
    IMG1_TAG=$(cat "${WORKSPACE}/info/pylibs-amd64_tag.txt")
    IMG2_TAG=$(cat "${WORKSPACE}/info/pylibs-arm64_tag.txt")
    STAGE_HASH="${IMG1_TAG##*-}"
    IMG_NAME="${DEFAULT_IMAGE_NAME}"
    IMG_TAG="pylibs-${STAGE_HASH}"
    echo "${IMG_TAG}" > "${WORKSPACE}/info/pylibs_tag.txt"
    docker manifest create "${IMG_NAME}:${IMG_TAG}" \
      --amend "${IMG_NAME}:${IMG1_TAG}" \
      --amend "${IMG_NAME}:${IMG2_TAG}"
    docker login -u "${DOCKER_USER}" -p "${DOCKER_PASS}";
    docker manifest push "${IMG_NAME}:${IMG_TAG}"
  fi
  PrintPaddedTextRight "Using Python/NPM Libs Image Tag" "${IMAGE_TAG}" "${COLOR_MSG_INFO}"
}

####################
# Determine the TAG to use and saves it in ${WORKSPACE}/info/version[_ci]_tag.txt.
# @ENV CIRCLE_BRANCH - the current git branch
# @ENV CIRCLE_TAG - the current tag, if any
function EnsureAppImageTagExists()
{
  BRANCH=${CIRCLE_BRANCH#*/}
  VERSION_STR=$(cat VERSION)
  if [[ -n $CIRCLE_TAG ]]; then
    VERSION_TAG="${CIRCLE_TAG#*v}"
  elif [[ "$BRANCH" == "develop" ]]; then
    VERSION_TAG="${VERSION_STR}-dev"
  elif [ "$BRANCH" != "master" ] && [ "$BRANCH" != "main" ]; then
    VERSION_TAG="ci-${VERSION_STR}-${BRANCH}"
  fi
  echo "${VERSION_TAG}" > "${WORKSPACE}/info/version_tag.txt"
  echo "Using tag: ${VERSION_TAG}";

  VERSION_CI=$(getVersionStr)
  echo "${VERSION_CI}" > "${WORKSPACE}/info/version_ci_tag.txt"
  echo "Using ci tag: ${VERSION_CI}";
}

####################
# Determine the image tag for "code stage" image based on its requirements file(s).
# Ensure the docker image tagged with the special tag exists; build if needed.
function EnsurePyAppImageExists()
{
  IMAGE_NAME="${DEFAULT_IMAGE_NAME}"
  IMG_STAGE="pyapp"
  DOCKERFILE2USE="docker/dfstage-${IMG_STAGE}.dockerfile"
  #IMAGE_TAG_HASH=$(CalcFileArgsMD5 "${DOCKERFILE2USE}" "$(GetImgStageFile "pylibs")" "${WORKSPACE}/info/version_tag.txt")
  #we want to always build this stage and not rely on a hash like prior stages; but keep script similar.
  IMAGE_TAG_HASH=$(cat "${WORKSPACE}/info/version_tag.txt")
  IMAGE_TAG="${IMG_STAGE}-${IMAGE_TAG_HASH}"
  echo "${IMAGE_TAG}" > "${WORKSPACE}/info/${IMG_STAGE}_tag.txt"

  FROM_STAGE_TAG=$(GetImgStageTag "pylibs")
  PrintPaddedTextRight "  Using PyLibs Tag" "${FROM_STAGE_TAG}" "${COLOR_MSG_INFO}"

  echo "Building Docker container ${IMAGE_NAME}:${IMAGE_TAG}…"
  multiArch_buildImages "${IMAGE_NAME}" "${IMAGE_TAG}"  "${DOCKERFILE2USE}" --no-cache \
    --build-arg "FROM_STAGE=${IMAGE_NAME}:${FROM_STAGE_TAG}" \
    --build-arg "VERSION_CI=${VERSION_CI}"

  "${UTILS_PATH}/pr-comment.sh" "Python App Image built: ${IMAGE_NAME}:${IMAGE_TAG}"
}

####################
# Build the version for the given arg.
# @param string $1 - the image name to build.
# @param string $2 - which Dockerfile version to use (rp|engage|generic).
# @param string $3 - the image tag to use.
# @param string $4 - the version tag to use when building the image; if empty, uses $3.
function BuildVersionForX()
{
  if [[ -z "$1" || "$1" == "default" ]]; then
    IMAGE_NAME=$DEFAULT_IMAGE_NAME
  else
    IMAGE_NAME=$1
  fi
  IMG_STAGE=$2
  IMG_TAG=$3
  if [[ -z "$4" ]]; then
    VER_TAG=${IMG_TAG}
  else
    VER_TAG=$4
  fi
  DOCKERFILE2USE="docker/final-${IMG_STAGE}.dockerfile"
  IMAGE_TAG=${IMG_TAG}
  echo "${IMAGE_TAG}" > "${WORKSPACE}/info/${IMG_STAGE}_tag.txt"
  FROM_STAGE_TAG=$(GetImgStageTag pyapp)
  PrintPaddedTextRight "  Using pyapp Tag" "${FROM_STAGE_TAG}" "${COLOR_MSG_INFO}"
  echo "Building Docker container ${IMAGE_NAME}:${IMAGE_TAG}…"
  multiArch_buildImages "${IMAGE_NAME}" "${IMAGE_TAG}" "${DOCKERFILE2USE}" --no-cache \
    --build-arg "FROM_STAGE_TAG=${FROM_STAGE_TAG}" \
    --build-arg "VERSION_TAG=${VER_TAG}"
  "${UTILS_PATH}/pr-comment.sh" "Image built: ${IMAGE_NAME}:${IMAGE_TAG}"
  PrintPaddedTextRight "Created Image" "${IMAGE_NAME}:${IMAGE_TAG}" "${COLOR_MSG_INFO}"
}

####################
# Build the version for generic Rapidpro.
# @param string $1 - the image tag to use.
function BuildVersionForRp()
{
  BuildVersionForX "${CIRCLE_PROJECT_USERNAME}/rapidpro" rp "$1"
}

####################
# Build the version for ourselves.
# @param string $1 - the image tag to use.
function BuildVersionForEngage()
{
  BuildVersionForX default engage "${1}"
  VERSION_CI_TAG=$(GetImgStageTag version_ci)
  BuildVersionForX default engage "${VERSION_CI_TAG}"
}

####################
# Build the version for generic use.
# @param string $1 - the image tag to use.
function BuildVersionForGeneric()
{
  IMAGE_NAME="${CIRCLE_PROJECT_USERNAME}/rapidpro"
  VERSION_CI=$(GetImgStageTag version_ci)
  VER_TAG=${VERSION_CI%-*}
  BuildVersionForX "${IMAGE_NAME}" generic "$1" "${VER_TAG}"
  BuildVersionForX "${IMAGE_NAME}" generic "${VER_TAG}"
}

####################
# Build the final image for the given type.
# @param string $1 - the image type name to build (engage|generic|rp).
# @param string $2 - the architecture being built (amd64|arm64).
function BuildImageForArch()
{
  IMG_STAGE=${1}
  if [[ "${IMG_STAGE}" == 'engage' || "${IMG_STAGE}" == 'pyapp' ]]; then
    IMAGE_NAME="${CIRCLE_PROJECT_USERNAME}/p4-engage"
  else
    IMAGE_NAME="${CIRCLE_PROJECT_USERNAME}/rapidpro"
  fi
  VERSION_TAG="$(cat workspace/info/version_tag.txt)"
  IMAGE_TAG="${VERSION_TAG}-${2}"
  if [[ "${IMG_STAGE}" != 'pyapp' ]]; then
    DOCKERFILE2USE="docker/final-${IMG_STAGE}.dockerfile"
  else
    DOCKERFILE2USE="docker/dfstage-${IMG_STAGE}.dockerfile"
  fi
  if [[ "${IMG_STAGE}" != 'pyapp' ]]; then
    FROM_STAGE_TAG=$(GetImgStageTag pyapp)
  else
    FROM_STAGE_TAG=$(GetImgStageTag pylibs)
  fi
  PrintPaddedTextRight "  Using From Tag" "${FROM_STAGE_TAG}" "${COLOR_MSG_INFO}"

  docker login -u "${DOCKER_USER}" -p "${DOCKER_PASS}"
  echo "Building Docker container ${IMAGE_NAME}:${IMAGE_TAG}…"
  buildImage "${IMAGE_NAME}" "${IMAGE_TAG}" "${DOCKERFILE2USE}" --no-cache \
    --build-arg "FROM_STAGE=${CIRCLE_PROJECT_USERNAME}/p4-engage:${FROM_STAGE_TAG}" \
    --build-arg "FROM_STAGE_TAG=${FROM_STAGE_TAG}" \
    --build-arg "VERSION_TAG=${VERSION_TAG}" \
    --build-arg "ARCH=${IMAGE_TAG##*-}/"
  docker push "${IMAGE_NAME}:${IMAGE_TAG}"
}

####################
# Create the manifest for the given type.
# @param string $1 - the image type name to build (engage|generic|rp).
function CreateManifestForImage()
{
  IMG_STAGE=${1}
  if [[ "${IMG_STAGE}" == 'engage' || "${IMG_STAGE}" == 'pyapp' ]]; then
    IMAGE_NAME="${CIRCLE_PROJECT_USERNAME}/p4-engage"
  elif [[ "${IMG_STAGE}" == 'generic' ]]; then
    IMAGE_NAME="${CIRCLE_PROJECT_USERNAME}/rapidpro"
  elif [[ "${IMG_STAGE}" == 'rp' ]]; then
    IMAGE_NAME="${CIRCLE_PROJECT_USERNAME}/rapidpro"
  fi
  IMAGE_TAG="$(cat workspace/info/version_tag.txt)"

  EnsureGitHubIsKnownHost
  docker login -u "${DOCKER_USER}" -p "${DOCKER_PASS}"
  echo "Creating Docker manifest for ${IMAGE_NAME}:${IMAGE_TAG}…"
  docker manifest create "${IMAGE_NAME}:${IMAGE_TAG}" \
    --amend "${IMAGE_NAME}:${IMAGE_TAG}-amd64" \
    --amend "${IMAGE_NAME}:${IMAGE_TAG}-arm64"
  docker manifest push "${IMAGE_NAME}:${IMAGE_TAG}"
  echo "Manifest built and pushed to DockerHub: ${IMAGE_NAME}:${IMAGE_TAG}"

  "${UTILS_PATH}/pr-comment.sh" "Container built: ${IMAGE_NAME}:${IMAGE_TAG}"

  if [[ "${IMG_STAGE}" == 'engage' ]]; then
    if [[ ${CIRCLE_BRANCH#*/} == "develop" ]]; then
      VER_TAG=ci-develop
      docker manifest create "${IMAGE_NAME}:${VER_TAG}" \
        --amend "${IMAGE_NAME}:${IMAGE_TAG}-amd64" \
        --amend "${IMAGE_NAME}:${IMAGE_TAG}-arm64"
      docker manifest push "${IMAGE_NAME}:${VER_TAG}"
    fi
  elif [[ "${IMG_STAGE}" == 'generic' ]]; then
    VERSION_CI=$(GetImgStageTag version_ci)
    VER_TAG=${VERSION_CI%-*}
    docker manifest create "${IMAGE_NAME}:${VER_TAG}" \
      --amend "${IMAGE_NAME}:${IMAGE_TAG}-amd64" \
      --amend "${IMAGE_NAME}:${IMAGE_TAG}-arm64"
    docker manifest push "${IMAGE_NAME}:${VER_TAG}"
  fi
}
