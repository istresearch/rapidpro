ARG FROM_STAGE
FROM ${FROM_STAGE} as load-files
# while doing the build, no interaction possible
ARG DEBIAN_FRONTEND=noninteractive

SHELL ["/bin/bash", "-c"]

ARG FLOW_EDITOR
ARG REPO_UN
ARG REPO_PW
# Check if the REPO_UN and REPO_PWD enviornment variables are set.  If not, exit build.
RUN function notify() { echo -e "\n----[ $1 ]----\n"; } \
 && if [ "${FLOW_EDITOR}" = "" ]; then echo "FLOW_EDITOR build arg not set"; exit 1; fi \
 && if [ "${REPO_UN}" = "" ]; then echo "REPO_PW build arg not set"; exit 1; fi \
 && if [ "${REPO_PW}" = "" ]; then echo "REPO_PW build arg not set"; exit 1; fi \
 && notify "using build from repo://engage/floweditor/floweditor-v${FLOW_EDITOR}_${ARCH}.tar.gz"
COPY https://${REPO_UN}:${REPO_PW}@repo.istresearch.com/engage/floweditor/floweditor-v${FLOW_EDITOR}_${ARCH}.tar.gz /opt/code2use/floweditor.tar.gz

COPY rp-build-deps.sh /opt/code2use/

COPY pyproject.toml /opt/code2use/
COPY poetry.lock /opt/code2use/
COPY poetry-install.sh /opt/code2use/

COPY .npmrc /opt/code2use/
COPY package*.json /opt/code2use/
COPY tailwind.config.js /opt/code2use/

RUN sed "s|poetry install|poetry install -vvv -n --no-dev|" /opt/code2use/poetry-install.sh > /opt/code2use/install-pylibs.sh \
 && chmod +x /opt/code2use/install-pylibs.sh

# ========================================================================

ARG FROM_STAGE
FROM ${FROM_STAGE}
# while doing the build, no interaction possible
ARG DEBIAN_FRONTEND=noninteractive

SHELL ["/bin/bash", "-c"]

ARG ARG_PIP_RETRIES=120
ARG ARG_PIP_TIMEOUT=400
ARG ARG_PIP_DEFAULT_TIMEOUT=400
ARG ARG_PIP_EXTRA_INDEX_URL=https://alpine-3.wheelhouse.praekelt.org/simple

ENV PIP_RETRIES=$ARG_PIP_RETRIES \
    PIP_TIMEOUT=$ARG_PIP_TIMEOUT \
    PIP_DEFAULT_TIMEOUT=$ARG_PIP_DEFAULT_TIMEOUT \
    PIP_EXTRA_INDEX_URL=$ARG_PIP_EXTRA_INDEX_URL \
    LIBRARY_PATH=/lib:/usr/lib

USER root

ARG USER_PID
RUN function notify() { echo -e "\n----[ $1 ]----\n"; } \
 && grp=engage; usr=engage && addgroup -S ${grp} && adduser -u ${USER_PID} -S ${usr} -G ${grp} \
 && mkdir -p /rapidpro; chown -R engage:engage /rapidpro \
 && mkdir -p /venv; chown -R engage:engage /venv \
 && notify "installed user:group [engage:engage]"

WORKDIR /rapidpro

COPY --from=load-files --chown=engage:engage /opt/code2use/* ./
# special folder for package*.json files when DEBUG mode is enabled and collectstatic is run.
COPY --from=load-files --chown=engage:engage /opt/code2use/package*.json ./node_config/

# required runtime libs
RUN function notify() { echo -e "\n----[ $1 ]----\n"; } \
 && apk -U add --virtual .my-build-deps \
    su-exec \
    cargo \
 && notify "installed needed OS libs required to build stuff" \
 && npm install -g npm@latest node-gyp less \
 && notify "installed/built global runtime npm libs" \
 && set -x; ./rp-build-deps.sh; set +x \
 && notify "installed/built OS libs" \
 && set -x; su-exec engage:engage ./install-pylibs.sh; set +x \
 && notify "installed/built python libs" \
 && su-exec engage:engage npm install \
 && tar -zxf floweditor.tar.gz --directory node_modules/@nyaruka/flow-editor \
 && notify "installed/built npm libs" \
 && apk del .rp-build-deps \
 && apk del .my-build-deps \
 && notify "removed libs only needed for building stuff"

RUN function notify() { echo -e "\n----[ $1 ]----\n"; } \
 && runDeps="$( \
    scanelf --needed --nobanner --recursive /venv \
      | awk '{ gsub(/,/, "\nso:", $2); print "so:" $2 }' \
      | sort -u \
      | xargs -r apk info --installed \
      | sort -u \
    )" \
 && apk --no-cache -U add $runDeps \
	libmagic \
	libressl \
	libxml2 \
	ncurses \
	pcre \
	postgresql-client \
 && notify "installed runtime pylibs"
