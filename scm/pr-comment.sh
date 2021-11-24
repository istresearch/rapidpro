#!/bin/bash
##########################################################################################
# Create a PR comment if we have a PR. Typically used to point a tester at a particular
# DockerHub container.
##########################################################################################

export SCRIPT_PATH=$(dirname "$0")
source "${SCRIPT_PATH}/utils.sh"


###############################################################################
# MAIN SCRIPT BODY
###############################################################################

# start off in our repo directory
cd ${REPO_PATH}

CreateGitPRComment "$1"
