# syntax=docker/dockerfile:1.2
ARG FROM_STAGE
FROM ${FROM_STAGE} as load-files
# while doing the build, no interaction possible
ARG DEBIAN_FRONTEND=noninteractive

WORKDIR /opt/code2use
COPY ./engage      engage
COPY ./locale      locale
COPY ./media       media
COPY ./static      static
COPY ./temba       temba
COPY ./templates   templates
COPY ./LICENSE     LICENSE
COPY ./manage.py   manage.py
COPY ./VERSION     VERSION
COPY ./staticfiles-hash-sh.txt .

ARG SF_HASH
RUN if [[ -n "${SF_HASH}" ]]; then \
 MRU_ENGAGE_FILE=$(find engage/static -type f ! -iname ".*" -exec stat --printf="%Y[%n]\n" "{}" \; | sort -nr | cut -d: -f2- | head -n1) \
 && MRU_RP_FILE=$(find static -type f ! -iname ".*" -exec stat --printf="%Y[%n]\n" "{}" \; | sort -nr | cut -d: -f2- | head -n1) \
 && echo "${MRU_ENGAGE_FILE}-${MRU_RP_FILE}" > staticfiles-hash-df.txt \
fi

# ========================================================================

ARG FROM_STAGE
FROM ${FROM_STAGE}
# while doing the build, no interaction possible
ARG DEBIAN_FRONTEND=noninteractive

# NOTE: we default force Celery to run as root; do we still wish to force that?
ARG ARG_C_FORCE_ROOT=1
ENV C_FORCE_ROOT=${ARG_C_FORCE_ROOT}

# 7.4.2 created on Jul 20, 2022 (2022.07.20)
ARG RAPIDPRO_VERSION=7.4.2
ENV RAPIDPRO_VERSION=${RAPIDPRO_VERSION}

USER root
# runtime libs we need/want to keep around
RUN apt-get update && apt-get install -y -q --no-install-recommends \
	rsync \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /rapidpro

COPY --from=load-files --chown=engage:engage /opt/code2use /opt/rp
RUN rsync -a /opt/rp/ ./ && rm -R /opt/rp

ARG UWSGI_PORT=8000
ARG UWSGI_NUM_WORKERS=16
# uwsgi timeout is in seconds
ARG UWSGI_TIMEOUT=45
# see https://uwsgi-docs.readthedocs.io/en/latest/LogFormat.html
# local app debug env option to suppress uwsgi access logs: - UWSGI_DISABLE_LOGGING=True
ENV UWSGI_VIRTUALENV=/venv \
    UWSGI_WSGI_FILE=temba/wsgi.py \
    UWSGI_HTTP=:${UWSGI_PORT} \
    UWSGI_MASTER=1 \
    UWSGI_WORKERS=${UWSGI_NUM_WORKERS} \
    UWSGI_HARAKIRI=${UWSGI_TIMEOUT} \
    UWSGI_LOGFORMAT_STRFTIME=true \
    UWSGI_LOG_DATE='%Y-%m-%dT%H:%M:%SZ' \
    UWSGI_LOGFORMAT='{"timestamp": "%(ftime)", "message": "access log", "level": "INFO", "app": "webserver", "message": "access log", "ip": "%(addr)", "http_method": "%(method)", "url": "%(uri)", "status": %(status), "size": %(size), "referrer": "%(referer)", "ua": "%(uagent)"}'
EXPOSE ${UWSGI_PORT}

# Enable HTTP 1.1 Keep Alive options for uWSGI (http-auto-chunked needed when ConditionalGetMiddleware not installed)
# These options don't appear to be configurable via environment variables, so pass them in here instead
ENV STARTUP_CMD="/venv/bin/uwsgi --http-auto-chunked --http-keepalive"

# apply overrides
COPY --chown=engage:engage docker/customizations/any /opt/ov/any
RUN rsync -a /opt/ov/any/ ./ && rm -R /opt/ov/any

COPY --chown=engage:engage docker/customizations/startup.sh /startup.sh
CMD ["/startup.sh"]

ARG VERSION_CI
ENV VERSION_CI=${VERSION_CI} \
    LC_ALL=en_US.UTF-8 \
    LANG=en_US.UTF-8

#NOTE: CANNOT UPDATE NODE!  arm64 build fails with
#COMPRESS_WITH_BROTLI=on
#+ python manage.py compress --extension=.haml --force -v0 --settings=temba.settings_compress_static
#CommandError: An error occurred during rendering channels/types/vonage/claim.haml: env: can't execute 'node': Exec format error
#The command '/bin/bash -c if [[ "${RUN_WEB_STATIC_FILE_COLLECTOR}" == "1" ]]; then   ./web-static.sh; fi' returned a non-zero code: 1
#::error::Build failed
#-------------
# Update Node 16.x to latest
#----------------------------------
# Install jq and curl dependencies
# Get major.minor version (that is v14.xx for node:14-alpine)
# Dynamically receive the newest version for the major version of this image
# Download the suitable tarball
# Uncompress the tarball
# Overwrite symlink node -> nodejs
#RUN function notify() { echo -e "\n----[ $1 ]----\n"; } \
# && apk update && apk add --no-cache jq curl \
# && export NODE_MAJOR_MINOR_VERSION=$(node --version | cut -d. -f1,2) \
# && export DOWNLOAD_VERSION=$(curl -fsSL --compressed https://unofficial-builds.nodejs.org/download/release/index.json | jq --raw-output ".[]|select(.version | startswith(\"$NODE_MAJOR_MINOR_VERSION\"))|.version" | head -1) \
# && curl -fsSLO --compressed "https://unofficial-builds.nodejs.org/download/release/$DOWNLOAD_VERSION/node-$DOWNLOAD_VERSION-linux-x64-musl.tar.xz" \
# && tar -xJf "node-$DOWNLOAD_VERSION-linux-x64-musl.tar.xz" -C /usr/local --strip-components=1 --no-same-owner \
# && ln -sf /usr/local/bin/node /usr/local/bin/nodejs \
# && notify "Node 16.x updated"

# Update openssl to latest
#----------------------------------
#RUN function notify() { echo -e "\n----[ $1 ]----\n"; } \
# && apk update && apk add --no-cache -u openssl \
# && notify "openssl updated"
