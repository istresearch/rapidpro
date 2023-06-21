#!/bin/bash

MRU_ENGAGE_FILE=$(find engage/static -type f ! -iname ".*" -exec stat --printf="%Y[%n]\n" "{}" \; | sort -nr | cut -d: -f2- | head -n1)
MRU_RP_FILE=$(find static -type f ! -iname ".*" -exec stat --printf="%Y[%n]\n" "{}" \; | sort -nr | cut -d: -f2- | head -n1)
echo "${MRU_ENGAGE_FILE}-${MRU_RP_FILE}" 2>&1 | tee staticfiles-hash-sh.txt
