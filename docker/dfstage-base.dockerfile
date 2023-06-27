# Debian 11.x image with Python 3.9 as default python3 install
FROM node:16-bullseye-slim

# while doing the build, no interaction possible
ARG DEBIAN_FRONTEND=noninteractive

SHELL ["/bin/bash", "-c"]

RUN function notify() { echo -e "\n----[ $1 ]----\n"; } \
 && apt-get update && apt-get install -y -q apt-utils && apt-get -y -q upgrade \
 && apt-get install -y -q \
    bash \
    nano \
    python3 \
	git \
    sqlite3 \
    curl \
    binutils \
    libproj-dev \
    gdal-bin \
    gdal-data \
    libgeos-3.9.0 \
    libgeos-c1v5 \
    libgdal28 \
    python3-gdal \
 && rm -rf /var/lib/apt/lists/* && apt-get clean \
 && LINK_DST="/usr/lib/libgdal.so"; if [[ ! -f "${LINK_DST}" ]]; then \
    LIB_LIST=($(find /usr -lname "$(basename ${LINK_DST}).*" -printf "%h/%l ")); \
    LINK_SRC=$(echo "${LIB_LIST}"); \
    ln -s "${LINK_SRC}" "${LINK_DST}"; \
 fi \
 && LINK_DST="/usr/lib/libgeos_c.so"; if [[ ! -f "${LINK_DST}" ]]; then \
    LIB_LIST=($(find /usr -lname "$(basename ${LINK_DST}).*" -printf "%h/%l ")); \
    LINK_SRC=$(echo "${LIB_LIST}"); \
    ln -s "${LINK_SRC}" "${LINK_DST}"; \
 fi \
 && notify "installed basic needs and runtime osgeo dependencies"

CMD ["/bin/bash"]
