#!/bin/bash

function hash_dir {
  find "${1}" -type f | LC_ALL=C sort |
  (
  while read -r name; do
      sha256sum "$name"
  done;
  ) | sha256sum
}

HASH_ENGAGE_DIR=$(hash_dir "engage/static")
HASH_TEMBA_DIR=$(hash_dir "static")
HASH_ALL=$(echo "${HASH_ENGAGE_DIR%%[[:space:]]*}-${HASH_TEMBA_DIR%%[[:space:]]*}" | sha256sum)
echo "${HASH_ALL%%[[:space:]]*}" 2>&1 | tee staticfiles-hash-all.txt
