ARG FROM_STAGE
ARG FROM_BUILD_LAYER=${FROM_STAGE}
FROM ${FROM_STAGE} as load-files
# while doing the build, no interaction possible
ARG DEBIAN_FRONTEND=noninteractive

RUN function notify() { echo -e "\n----[ $1 ]----\n"; } \
 && apt-get update && apt-get install -y -q --no-install-recommends \
    gettext \
    rsync \
 && notify "installed needed OS libs"

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

# apply overrides
COPY docker/customizations/any /opt/ov/any
RUN rsync -a /opt/ov/any/ /opt/code2use/

# apply translations (needs gettext OS lib)
RUN function notify() { echo -e "\n----[ $1 ]----\n"; } \
 && set -x; ./web-i18n.sh; set +x \
 && notify "translations compiled"

# ========================================================================

# optional stage in case we already have a collection of static files to use
FROM ${FROM_STAGE} as tar_download
ARG REPO_UN
ARG REPO_PW
ARG REPO_HOST
ARG REPO_FILEPATH
ONBUILD RUN echo "download tar"
ONBUILD ADD --chown=engage:engage "https://${REPO_UN}:${REPO_PW}@${REPO_HOST}/${REPO_FILEPATH}" /rapidpro

# ========================================================================

FROM ${FROM_BUILD_LAYER}
# while doing the build, no interaction possible
ARG DEBIAN_FRONTEND=noninteractive

# NOTE: we default force Celery to run as root
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

ARG VERSION_CI
ENV VERSION_CI=${VERSION_CI} \
    LC_ALL=en_US.UTF-8 \
    LANG=en_US.UTF-8

CMD ["./startup.sh"]
