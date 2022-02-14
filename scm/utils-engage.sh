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
# @param string $1 - the base image to use.
function EnsureGeosImage()
{
  if [[ -z "$1" ]]; then
    IMAGE_NAME=$DEFAULT_IMAGE_NAME
  else
    IMAGE_NAME=$1
  fi
  IMG_STAGE=pygeos
  DOCKERFILE2USE=docker/Dockerfile.${IMG_STAGE}
  IMAGE_TAG=${IMG_STAGE}-`CalcFileArgsMD5 "${DOCKERFILE2USE}"`
  echo $IMAGE_TAG > "${UTILS_PATH}/${IMG_STAGE}_tag.txt"
  if ! DockerImageTagExists $IMAGE_NAME $IMAGE_TAG; then
    echo "Building Docker container $IMAGE_NAME:$IMAGE_TAG..."
    #if debugging, can add arg --progress=plain to the docker build command
    docker build \
        -t $IMAGE_NAME:$IMAGE_TAG -f ${DOCKERFILE2USE} .
    docker push $IMAGE_NAME:$IMAGE_TAG
    "${UTILS_PATH}/pr-comment.sh" "Base osgeo.org GEO Libs Image built: $IMAGE_NAME:$IMAGE_TAG"
  fi
  PrintPaddedTextRight "Using Base osgeo.org GEO Libs Image Tag" $IMAGE_TAG ${COLOR_MSG_INFO}
}

####################
# Determine the image tag for Python Libs image based on its requirements file(s).
# Ensure the docker image tagged with the special tag exists; build if needed.
# @param string $1 - the base image to use.
function EnsurePyLibsImage()
{
  if [[ -z "$1" ]]; then
    IMAGE_NAME=$DEFAULT_IMAGE_NAME
  else
    IMAGE_NAME=$1
  fi
  IMG_STAGE=pylibs
  DOCKERFILE2USE=docker/Dockerfile.${IMG_STAGE}
  IMAGE_TAG=${IMG_STAGE}-`CalcFileArgsMD5 "${DOCKERFILE2USE}" "$(GetImgStageFile pygeos)" "poetry.lock" "pyproject.toml" "package-lock.json" "package.json"`
  echo $IMAGE_TAG > "${UTILS_PATH}/${IMG_STAGE}_tag.txt"
  if ! DockerImageTagExists $IMAGE_NAME $IMAGE_TAG; then
    FROM_STAGE_TAG=`GetImgStageTag pygeos`
    PrintPaddedTextRight "  Using pygeos Tag" $FROM_STAGE_TAG ${COLOR_MSG_INFO}
    echo "Building Docker container ${IMAGE_NAME}:${IMAGE_TAG}..."
    #if debugging, can add arg --progress=plain or --no-cache  to the docker build command
    docker build --build-arg FROM_STAGE_TAG=$FROM_STAGE_TAG \
        -t $IMAGE_NAME:$IMAGE_TAG -f ${DOCKERFILE2USE} .
    docker push $IMAGE_NAME:$IMAGE_TAG
    "${UTILS_PATH}/pr-comment.sh" "Python/NPM Libs Image built: $IMAGE_NAME:$IMAGE_TAG"
  fi
  PrintPaddedTextRight "Using Python/NPM Libs Image Tag" $IMAGE_TAG ${COLOR_MSG_INFO}
}

####################
# Determine the image tag for "code stage" image based on its requirements file(s).
# Ensure the docker image tagged with the special tag exists; build if needed.
# @param string $1 - the base image to use.
function EnsurePyAppImage()
{
  if [[ -z "$1" || "$1" == "default" ]]; then
    IMAGE_NAME=$DEFAULT_IMAGE_NAME
  else
    IMAGE_NAME=$1
  fi
  IMG_STAGE=pyapp
  IMAGE_TAG=${IMG_STAGE}-$2
  DOCKERFILE2USE=docker/Dockerfile.${IMG_STAGE}
  echo $IMAGE_TAG > "${UTILS_PATH}/${IMG_STAGE}_tag.txt"
  FROM_STAGE_TAG=`GetImgStageTag pylibs`
  PrintPaddedTextRight "  Using pylibs Tag" $FROM_STAGE_TAG ${COLOR_MSG_INFO}
  echo "Building Docker container ${IMAGE_NAME}:${IMAGE_TAG}..."

  set -x
  getVersionStr
  VERSION_CI=${VERSION_STR}

  #if debugging, can add arg --progress=plain to the docker build command
  docker build --build-arg FROM_STAGE_TAG=$FROM_STAGE_TAG \
      --build-arg VERSION_CI=$VERSION_CI \
      -t $IMAGE_NAME:$IMAGE_TAG -f ${DOCKERFILE2USE} .
  docker push $IMAGE_NAME:$IMAGE_TAG
  "${UTILS_PATH}/pr-comment.sh" "Python App Image built: $IMAGE_NAME:$IMAGE_TAG"
}

####################
# Build the version for the given arg.
# @param string $1 - the image name to build.
# @param string $1 - which Dockerfile version to use (rp|engage|generic).
# @param string $2 - the version tag to create.
function BuildVersionForX()
{
  if [[ -z "$1" || "$1" == "default" ]]; then
    IMAGE_NAME=$DEFAULT_IMAGE_NAME
  else
    IMAGE_NAME=$1
  fi
  IMG_TAG=$3
  IMG_STAGE=$2
  DOCKERFILE2USE=docker/Dockerfile.${IMG_STAGE}
  IMAGE_TAG=${IMG_TAG}
  echo $IMAGE_TAG > "${UTILS_PATH}/${IMG_STAGE}_tag.txt"
  #always build, don't bother checking if it already exists.
  #if ! DockerImageTagExists $IMAGE_NAME $IMAGE_TAG; then
    FROM_STAGE_TAG=`GetImgStageTag pyapp`
    PrintPaddedTextRight "  Using pyapp Tag" $FROM_STAGE_TAG ${COLOR_MSG_INFO}
    echo "Building Docker container ${IMAGE_NAME}:${IMAGE_TAG}..."
    #if debugging, can add arg --progress=plain to the docker build command
    docker build --build-arg FROM_STAGE_TAG=$FROM_STAGE_TAG \
        --build-arg VERSION_TAG=$IMG_TAG \
        -t $IMAGE_NAME:$IMAGE_TAG -f ${DOCKERFILE2USE} .
    docker push $IMAGE_NAME:$IMAGE_TAG
    "${UTILS_PATH}/pr-comment.sh" "Image built: $IMAGE_NAME:$IMAGE_TAG"
  #fi
  PrintPaddedTextRight "Created Image" "$IMAGE_NAME:$IMAGE_TAG" ${COLOR_MSG_INFO}
}

####################
# Build the version for generic Rapidpro.
# @param string $1 - the version to tag.
function BuildVersionForRp()
{
  BuildVersionForX "istresearch/rapidpro" rp $1
}

####################
# Build the version for ourselves.
# @param string $1 - the base image to use.
# @param string $2 - the version to tag.
function BuildVersionForEngage()
{
  BuildVersionForX default engage $1
}

####################
# Build the version for generic use.
# @param string $1 - the base image to use.
# @param string $2 - the version to tag.
function BuildVersionForGeneric()
{
  BuildVersionForX "istresearch/rapidpro" generic $1
}



