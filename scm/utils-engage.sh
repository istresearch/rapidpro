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

DEFAULT_IMAGE_NAME=istresearch/p4-engage


####################
# Get the file containing the image tag  for stage image specified by arg.
# @param string $1 - the stage image base name.
function GetImgStageFile()
{
  IMG_STAGE=$1
  echo "${UTILS_PATH}/${IMG_STAGE}_tag.txt"
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
# Determine the image tag for Python3 & GEOS image based on its requirements file(s).
# Ensure the docker image tagged with the special tag exists; build if needed.
# @param string $1 - the base image to use, "default" will use var $DEFAULT_IMAGE_NAME.
# @param string $2 - flag to build multi-arch images or just standard.
function EnsureGeosImage()
{
  if [[ -z "$1" || "$1" == "default" ]]; then
    IMAGE_NAME=$DEFAULT_IMAGE_NAME
  else
    IMAGE_NAME=$1
  fi
  USE_MULTIARCH="${2:-false}"
  IMG_STAGE=pygeos
  DOCKERFILE2USE=docker/Dockerfile.${IMG_STAGE}
  IMAGE_TAG_HASH=$(CalcFileArgsMD5 "${DOCKERFILE2USE}")
  if [[ ${USE_MULTIARCH} == "false" ]]; then
    IMAGE_TAG="${IMG_STAGE}-${IMAGE_TAG_HASH}"
  else
    IMAGE_TAG="${IMG_STAGE}-ma-${IMAGE_TAG_HASH}"
  fi
  echo "${IMAGE_TAG}" > "${UTILS_PATH}/${IMG_STAGE}_tag.txt"
  if ! DockerImageTagExists "${IMAGE_NAME}" "${IMAGE_TAG}"; then
    echo "Building Docker container ${IMAGE_NAME}:${IMAGE_TAG}…"
    if [[ ${USE_MULTIARCH} == "false" ]]; then
      buildImage "${IMAGE_NAME}" "${IMAGE_TAG}" "${DOCKERFILE2USE}"
    else
      multiArch_buildImages "${IMAGE_NAME}" "${IMAGE_TAG}" "${DOCKERFILE2USE}"
    fi
    "${UTILS_PATH}/pr-comment.sh" "Base osgeo.org GEO Libs Image built: ${IMAGE_NAME}:${IMAGE_TAG}"
  fi
  PrintPaddedTextRight "Using Base osgeo.org GEO Libs Image Tag" "${IMAGE_TAG}" "${COLOR_MSG_INFO}"
}

####################
# Determine the image tag for Python Libs image based on its requirements file(s).
# Ensure the docker image tagged with the special tag exists; build if needed.
# @param string $1 - the base image to use, "default" will use var $DEFAULT_IMAGE_NAME.
# @param string $2 - flag to build multi-arch images or just standard.
function EnsurePyLibsImage()
{
  if [[ -z "$1" || "$1" == "default" ]]; then
    IMAGE_NAME=$DEFAULT_IMAGE_NAME
  else
    IMAGE_NAME=$1
  fi
  USE_MULTIARCH="${2:-false}"
  IMG_STAGE=pylibs
  DOCKERFILE2USE=docker/Dockerfile.${IMG_STAGE}
  IMAGE_TAG_HASH=$(CalcFileArgsMD5 "${DOCKERFILE2USE}" "$(GetImgStageFile pygeos)" "poetry.lock" "pyproject.toml" "package-lock.json" "package.json")
  if [[ ${USE_MULTIARCH} == "false" ]]; then
    IMAGE_TAG="${IMG_STAGE}-${IMAGE_TAG_HASH}"
  else
    IMAGE_TAG="${IMG_STAGE}-ma-${IMAGE_TAG_HASH}"
  fi
  echo "${IMAGE_TAG}" > "${UTILS_PATH}/${IMG_STAGE}_tag.txt"
  if ! DockerImageTagExists "${IMAGE_NAME}" "${IMAGE_TAG}"; then
    FROM_STAGE_TAG=$(GetImgStageTag pygeos)
    PrintPaddedTextRight "  Using pygeos Tag" "${FROM_STAGE_TAG}" "${COLOR_MSG_INFO}"
    echo "Building Docker container ${IMAGE_NAME}:${IMAGE_TAG}…"
    if [[ ${USE_MULTIARCH} == "false" ]]; then
      buildImage "${IMAGE_NAME}" "${IMAGE_TAG}"  "${DOCKERFILE2USE}" \
        --build-arg "FROM_STAGE_TAG=${FROM_STAGE_TAG}"
    else
      multiArch_buildImages "${IMAGE_NAME}" "${IMAGE_TAG}"  "${DOCKERFILE2USE}" \
        --build-arg "FROM_STAGE_TAG=${FROM_STAGE_TAG}"
    fi
    "${UTILS_PATH}/pr-comment.sh" "Python/NPM Libs Image built: ${IMAGE_NAME}:${IMAGE_TAG}"
  fi
  PrintPaddedTextRight "Using Python/NPM Libs Image Tag" ${IMAGE_TAG} "${COLOR_MSG_INFO}"
}

####################
# Determine the image tag for "code stage" image based on its requirements file(s).
# Ensure the docker image tagged with the special tag exists; build if needed.
# @param string $1 - the base image to use, "default" will use var $DEFAULT_IMAGE_NAME.
# @param string $2 - flag to build multi-arch images or just standard.
function EnsurePyAppImage()
{
  if [[ -z "$1" || "$1" == "default" ]]; then
    IMAGE_NAME=$DEFAULT_IMAGE_NAME
  else
    IMAGE_NAME=$1
  fi
  USE_MULTIARCH="${2:-false}"
  IMG_STAGE=pyapp
  DOCKERFILE2USE=docker/Dockerfile.${IMG_STAGE}
  IMAGE_TAG_HASH=$(cat ${UTILS_PATH}/version_tag.txt)
  if [[ ${USE_MULTIARCH} == "false" ]]; then
    IMAGE_TAG="${IMG_STAGE}-${IMAGE_TAG_HASH}"
  else
    IMAGE_TAG="${IMG_STAGE}-ma-${IMAGE_TAG_HASH}"
  fi
  echo "${IMAGE_TAG}" > "${UTILS_PATH}/${IMG_STAGE}_tag.txt"
  FROM_STAGE_TAG=$(GetImgStageTag pylibs)
  PrintPaddedTextRight "  Using pylibs Tag" "${FROM_STAGE_TAG}" "${COLOR_MSG_INFO}"
  echo "Building Docker container ${IMAGE_NAME}:${IMAGE_TAG}…"
  if [[ ${USE_MULTIARCH} == "false" ]]; then
    buildImage "${IMAGE_NAME}" "${IMAGE_TAG}" "${DOCKERFILE2USE}" --no-cache \
      --build-arg "FROM_STAGE_TAG=${FROM_STAGE_TAG}" \
      --build-arg "VERSION_CI=${VERSION_CI}"
  else
    multiArch_buildImages "${IMAGE_NAME}" "${IMAGE_TAG}" "${DOCKERFILE2USE}" --no-cache \
      --build-arg "FROM_STAGE_TAG=${FROM_STAGE_TAG}" \
      --build-arg "VERSION_CI=${VERSION_CI}"
  fi
  "${UTILS_PATH}/pr-comment.sh" "Python App Image built: ${IMAGE_NAME}:${IMAGE_TAG}"
}

####################
# Build the version for the given arg.
# @param string $1 - the image name to build.
# @param string $2 - which Dockerfile version to use (rp|engage|generic).
# @param string $3 - the image tag to use.
# @param string $4 - the version tag to use when building the image; if empty, uses $3.
# @param string $5 - flag to build multi-arch images or just standard.
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
  USE_MULTIARCH="${5:-false}"
  DOCKERFILE2USE=docker/Dockerfile.${IMG_STAGE}
  IMAGE_TAG=${IMG_TAG}
  echo "${IMAGE_TAG}" > "${UTILS_PATH}/${IMG_STAGE}_tag.txt"
  FROM_STAGE_TAG=$(GetImgStageTag pyapp)
  PrintPaddedTextRight "  Using pyapp Tag" "${FROM_STAGE_TAG}" "${COLOR_MSG_INFO}"
  echo "Building Docker container ${IMAGE_NAME}:${IMAGE_TAG}…"
  if [[ ${USE_MULTIARCH} == "false" ]]; then
    buildImage "${IMAGE_NAME}" "${IMAGE_TAG}" "${DOCKERFILE2USE}" --no-cache \
      --build-arg "FROM_STAGE_TAG=${FROM_STAGE_TAG}" \
      --build-arg "VERSION_TAG=${VER_TAG}"
  else
    multiArch_buildImages "${IMAGE_NAME}" "${IMAGE_TAG}" "${DOCKERFILE2USE}" --no-cache \
      --build-arg "FROM_STAGE_TAG=${FROM_STAGE_TAG}" \
      --build-arg "VERSION_TAG=${VER_TAG}"
  fi
  "${UTILS_PATH}/pr-comment.sh" "Image built: ${IMAGE_NAME}:${IMAGE_TAG}"
  PrintPaddedTextRight "Created Image" "${IMAGE_NAME}:${IMAGE_TAG}" "${COLOR_MSG_INFO}"
}

####################
# Build the version for generic Rapidpro.
# @param string $1 - the image tag to use.
# @param string $2 - flag to build multi-arch images or just standard.
function BuildVersionForRp()
{
  BuildVersionForX "istresearch/rapidpro" rp "$1" "" "$2"
}

####################
# Build the version for ourselves.
# @param string $1 - the image tag to use.
# @param string $2 - flag to build multi-arch images or just standard.
function BuildVersionForEngage()
{
  BuildVersionForX default engage "$1" "" "$2"

  USE_MULTIARCH="${2:-false}"
  if [[ ${USE_MULTIARCH} == "false" ]]; then
    IMAGE_NAME=$DEFAULT_IMAGE_NAME
    VERSION_CI_TAG=$(GetImgStageTag version_ci)
    docker tag "${IMAGE_NAME}:$1" "${IMAGE_NAME}:${VERSION_CI_TAG}"
    docker push "${IMAGE_NAME}:${VERSION_CI_TAG}"
    PrintPaddedTextRight "Created Image" "${IMAGE_NAME}:${VERSION_CI_TAG}" "${COLOR_MSG_INFO}"
  fi
}

####################
# Build the version for generic use.
# @param string $1 - the image tag to use.
# @param string $2 - flag to build multi-arch images or just standard.
function BuildVersionForGeneric()
{
  IMAGE_NAME="istresearch/rapidpro"
  VERSION_CI=$(GetImgStageTag version_ci)
  VER_TAG=${VERSION_CI%-*}
  BuildVersionForX "${IMAGE_NAME}" generic "$1" "${VER_TAG}" "$2"

  USE_MULTIARCH="${2:-false}"
  if [[ ${USE_MULTIARCH} == "false" ]]; then
    docker tag "${IMAGE_NAME}:$1" "${IMAGE_NAME}:${VER_TAG}"
    docker push "${IMAGE_NAME}:${VER_TAG}"
    PrintPaddedTextRight "Created Image" "${IMAGE_NAME}:${VER_TAG}" "${COLOR_MSG_INFO}"
  fi
}

####################
# Determine the TAG to use and saves it in ${UTILS_PATH}/version_tag.txt.
# @ENV CIRCLE_BRANCH - the current git branch
# @ENV CIRCLE_TAG - the current tag, if any
function determine_image_tag()
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
  echo "${VERSION_TAG}" > "${UTILS_PATH}/version_tag.txt"

  VERSION_CI=$(getVersionStr)
  echo "${VERSION_CI}" > "${UTILS_PATH}/version_ci_tag.txt"
}
