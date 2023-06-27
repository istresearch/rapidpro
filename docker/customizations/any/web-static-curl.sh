#!/bin/bash

echo "download tar file"
TAR_URL="https://${REPO_DL_DOMAIN}/${REPO_FILEPATH}"
####################################################
# NOTE: curl with user/pw in URL will show in run logs, hide it.
# bash sub-shell magic to avoid exposing the pw in cmd line history via inline file-create & use.
# @see https://stackoverflow.com/questions/33794842/forcing-curl-to-get-a-password-from-the-environment
curl --remote-name --netrc-file <(cat <<<"machine ${REPO_DL_DOMAIN} login ${REPO_UN} password ${REPO_PW}") "${TAR_URL}"
TAR_FILE=$(basename "${REPO_FILEPATH}")
if [ -f "${TAR_FILE}" ]; then
 tar -xzf "${TAR_FILE}"
 rm "${TAR_FILE}"
else
  echo "download failed"
  exit 1
fi
