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


####################
# Determine the image tag for Python3 & GEOS image based on its requirements file(s).
# Ensure the docker image tagged with the special tag exists; build if needed.
# @param string $1 - the base image to use.
function EnsureGeosImage()
{
  IMAGE_NAME=$1
  IMAGE_TAG=pygeos-`CalcFileArgsMD5 "docker/Dockerfile.pygeos" "docker/geolibs.sh"`
  echo $IMAGE_TAG >> "${UTILS_PATH}/pygeos_tag.txt"
  if ! DockerImageTagExists $IMAGE_NAME $IMAGE_TAG; then
    echo "Building Docker container $IMAGE_NAME:$IMAGE_TAG..."
    docker build -t $IMAGE_NAME:$IMAGE_TAG -f docker/Dockerfile.pygeos .
    docker push $IMAGE_NAME:$IMAGE_TAG
    "${UTILS_PATH}/pr-comment.sh" "Python3/GEOS Image built: $IMAGE_NAME:$IMAGE_NAME"
  fi
  PrintPaddedTextRight "Using Python3/GEOS Image Tag" $IMAGE_TAG ${COLOR_MSG_INFO}
}

####################
# Determine the image tag for Libs image based on its requirements file(s).
# Ensure the docker image tagged with the special tag exists; build if needed.
# @param string $1 - the base image to use.
function EnsureLibsImage()
{
  IMAGE_NAME=$1
  IMAGE_TAG=uilibs-`CalcFileArgsMD5 "pip-freeze.txt" "pip-add-reqs.txt" "package-lock.json"`
  echo $IMAGE_TAG >> "${UTILS_PATH}/uilibs_tag.txt"
  if ! DockerImageTagExists $IMAGE_NAME $IMAGE_TAG; then
    if [[ ! -f "${UTILS_PATH}/pygeos_tag.txt" ]]; then
      echo "Error: ${UTILS_PATH}/pygeos_tag.txt not found."
      exit 2
    fi
    PYGEOS_TAG=`cat ${UTILS_PATH}/pygeos_tag.txt`
    echo "Building Docker container ${IMAGE_NAME}:${IMAGE_TAG} from :${PYGEOS_TAG}..."
    docker build --build-arg FROM_PYGEOS_TAG=${PYGEOS_TAG} -t $IMAGE_NAME:$IMAGE_TAG -f docker/Dockerfile.uilibs .
    docker push $IMAGE_NAME:$IMAGE_TAG
    "${UTILS_PATH}/pr-comment.sh" "UI Libs Image built: $IMAGE_NAME:$IMAGE_NAME"
  fi
  PrintPaddedTextRight "Using UI Libs Image Tag" $IMAGE_TAG ${COLOR_MSG_INFO}
}
