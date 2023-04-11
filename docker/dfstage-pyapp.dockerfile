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

# ========================================================================

ARG FROM_STAGE
FROM ${FROM_STAGE}
# while doing the build, no interaction possible
ARG DEBIAN_FRONTEND=noninteractive

# NOTE: we default force Celery to run as root; do we still wish to force that?
ARG ARG_C_FORCE_ROOT=1
ENV C_FORCE_ROOT=${ARG_C_FORCE_ROOT}

ARG RAPIDPRO_VERSION=7.4.2
ENV RAPIDPRO_VERSION=${RAPIDPRO_VERSION}

USER root
# runtime libs we need/want to keep around
RUN apk add --update --no-cache \
	rsync \
 && rm -rf /var/cache/apk/*

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

ENV CELERY_CMD="/venv/bin/celery --beat --app=temba worker --loglevel=INFO --queues=celery,msgs,flows,handler"

# apply overrides
COPY --chown=engage:engage docker/customizations/any /opt/ov/any
RUN rsync -a /opt/ov/any/ ./ && rm -R /opt/ov/any

COPY --chown=engage:engage docker/customizations/startup.sh /startup.sh
CMD ["/startup.sh"]
USER engage

ARG VERSION_CI
ENV VERSION_CI=${VERSION_CI}
