ARG FROM_STAGE

ARG ARG_PIP_RETRIES=120
ARG ARG_PIP_TIMEOUT=400
ARG ARG_PIP_DEFAULT_TIMEOUT=400
ARG ARG_PIP_EXTRA_INDEX_URL=https://alpine-3.wheelhouse.praekelt.org/simple

ARG USER_PID=1717

# ========================================================================

FROM alpine as load-files

COPY pyproject.toml /opt/code2use/
COPY package*.json /opt/code2use/
COPY poetry-install.sh /opt/code2use/
COPY rp-build-deps.sh /opt/code2use/

RUN sed "s|poetry install|poetry install -vv -n|" /opt/code2use/poetry-install.sh > /opt/code2use/install-pylibs.sh \
 && chmod +x /opt/code2use/install-pylibs.sh

# ========================================================================

ARG FROM_STAGE
FROM ${FROM_STAGE}

# Colors! :D
ENV COLOR_NONE=\033[0m \
	COLOR_GREEN=\033[0;32m \
	COLOR_RED=\033[0;31m \
	COLOR_CYAN=\033[0;36m
# Once colors have been defined, we can use them for specific things.
ENV COLOR_MSG=$COLOR_CYAN

# while doing the build, no interaction possible
ENV DEBIAN_FRONTEND noninteractive

ARG ARG_PIP_RETRIES
ARG ARG_PIP_TIMEOUT
ARG ARG_PIP_DEFAULT_TIMEOUT
ARG ARG_PIP_EXTRA_INDEX_URL

ENV PIP_RETRIES=$ARG_PIP_RETRIES \
    PIP_TIMEOUT=$ARG_PIP_TIMEOUT \
    PIP_DEFAULT_TIMEOUT=$ARG_PIP_DEFAULT_TIMEOUT \
    PIP_EXTRA_INDEX_URL=$ARG_PIP_EXTRA_INDEX_URL \
    LIBRARY_PATH=/lib:/usr/lib

USER root

ARG USER_PID
RUN grp=engage; usr=engage && addgroup -S $grp && adduser -u $USER_PID -S $usr -G $grp \
 && mkdir -p /rapidpro; chown -R engage:engage /rapidpro \
 && mkdir -p /venv; chown -R engage:engage /venv

WORKDIR /rapidpro

COPY --from=load-files --chown=engage:engage /opt/code2use/* ./

# required runtime libs
RUN set -ex; apk -U add --virtual .my-build-deps \
    su-exec \
    gcc \
    linux-headers \
    libressl-dev \
    libxslt-dev \
    libxml2-dev \
    libffi-dev \
    python3-dev \
    musl-dev \
    postgresql-dev \
 && echo "installed all runtime deps" \
 && npm install -g node-gyp less \
 && echo "installed global runtime npm libs" \
 && ./rp-build-deps.sh \
 && set -x; su-exec engage:engage ./install-pylibs.sh \
 && su-exec engage:engage npm install \
 && apk del .rp-build-deps \
 && apk del .my-build-deps \
 && echo "installed/built python and npm libs"

RUN runDeps="$( \
    scanelf --needed --nobanner --recursive /venv \
      | awk '{ gsub(/,/, "\nso:", $2); print "so:" $2 }' \
      | sort -u \
      | xargs -r apk info --installed \
      | sort -u \
    )" \
 && apk --no-cache -U add $runDeps \
	git \
	libmagic \
	libressl \
	libxml2 \
	ncurses \
	pcre \
	postgresql-client \
 && echo "installed runtime pylibs"
