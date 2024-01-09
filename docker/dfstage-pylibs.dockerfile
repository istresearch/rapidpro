ARG FROM_STAGE
FROM ${FROM_STAGE} as load-files
# while doing the build, no interaction possible
ARG DEBIAN_FRONTEND=noninteractive

SHELL ["/bin/bash", "-c"]

ARG ARCH
ARG FLOW_EDITOR
ARG REPO_UN
ARG REPO_PW
# Check if the REPO_UN and REPO_PWD enviornment variables are set.  If not, exit build.
RUN function notify() { echo -e "\n----[ $1 ]----\n"; } \
 && if [ "${FLOW_EDITOR}" = "" ]; then echo "FLOW_EDITOR build arg not set"; exit 1; fi \
 && if [ "${REPO_UN}" = "" ]; then echo "REPO_PW build arg not set"; exit 1; fi \
 && if [ "${REPO_PW}" = "" ]; then echo "REPO_PW build arg not set"; exit 1; fi \
 && notify "using build from repo://engage/floweditor/floweditor-v${FLOW_EDITOR}_${ARCH}.tar.gz"
ADD https://${REPO_UN}:${REPO_PW}@repo.istresearch.com/engage/floweditor/floweditor-v${FLOW_EDITOR}_${ARCH}.tar.gz /opt/code2use/floweditor.tar.gz

COPY pyproject.toml /opt/code2use/
COPY poetry.lock /opt/code2use/
COPY poetry-install.sh /opt/code2use/

COPY .npmrc /opt/code2use/
COPY package*.json /opt/code2use/
COPY tailwind.config.js /opt/code2use/

RUN sed "s|poetry install|poetry install -vv -n --only main|" /opt/code2use/poetry-install.sh > /opt/code2use/install-pylibs.sh \
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
#ARG ARG_PIP_EXTRA_INDEX_URL=https://bullseye.wheelhouse.praekelt.org/simple
ARG ARG_PIP_EXTRA_INDEX_URL

ENV PIP_RETRIES=$ARG_PIP_RETRIES \
    PIP_TIMEOUT=$ARG_PIP_TIMEOUT \
    PIP_DEFAULT_TIMEOUT=$ARG_PIP_DEFAULT_TIMEOUT \
    PIP_EXTRA_INDEX_URL=$ARG_PIP_EXTRA_INDEX_URL \
    LIBRARY_PATH=/lib:/usr/lib

USER root

ARG USER_PID=1717
RUN function notify() { echo -e "\n----[ $1 ]----\n"; } \
 && grp=engage; usr=engage && addgroup --system ${grp} && adduser --uid ${USER_PID} --ingroup ${grp} ${usr} \
 && mkdir -p /rapidpro; chown -R engage:engage /rapidpro \
 && mkdir -p /venv; chown -R engage:engage /venv \
 && notify "installed user:group [engage:engage]"

WORKDIR /rapidpro

COPY --from=load-files --chown=engage:engage /opt/code2use/* ./
# special folder for package*.json files when DEBUG mode is enabled and collectstatic is run.
COPY --from=load-files --chown=engage:engage /opt/code2use/package*.json ./node_config/

# Install latest su-exec
RUN function notify() { echo -e "\n----[ $1 ]----\n"; } \
 && set -ex; \
  curl -o /usr/local/bin/su-exec.c https://raw.githubusercontent.com/ncopa/su-exec/master/su-exec.c; \
  fetch_deps='gcc libc-dev'; \
  apt-get update; \
  apt-get install -y -q --no-install-recommends $fetch_deps; \
  rm -rf /var/lib/apt/lists/*; \
  gcc -Wall /usr/local/bin/su-exec.c -o/usr/local/bin/su-exec; \
  chown root:root /usr/local/bin/su-exec; \
  chmod 0755 /usr/local/bin/su-exec; \
  rm /usr/local/bin/su-exec.c; \
  apt-get purge -y --auto-remove $fetch_deps \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/* \
 && notify "installed su-exec"

RUN function notify() { echo -e "\n----[ $1 ]----\n"; } \
 && apt-get update && apt-get install -y -q --no-install-recommends \
    cargo \
    git \
 && rm -rf /var/lib/apt/lists/* && apt-get clean \
 && notify "installed needed OS libs required"

RUN function notify() { echo -e "\n----[ $1 ]----\n"; } \
 && npm install -g node-gyp less \
 && notify "installed/built global runtime npm libs" \
 && su-exec engage:engage npm install \
 && tar -zxf floweditor.tar.gz --directory node_modules/@nyaruka/flow-editor \
 && notify "installed/built npm libs"

RUN function notify() { echo -e "\n----[ $1 ]----\n"; } \
 && apt-get update && apt-get install -y -q --no-install-recommends \
    libfreetype-dev \
    libmagic-dev \
    libncurses5-dev libncursesw5-dev \
    libpcre2-posix2 libpcre2-dev \
    libpng-dev \
    libxml2-dev \
    libxslt1-dev \
    locales \
    locales-all \
    ncurses-dev \
    pax-utils \
    postgresql-client \
    python3-dev \
    python3-venv \
    python3.9 \
 && rm -rf /var/lib/apt/lists/* && apt-get clean \
 && locale-gen en_US.UTF-8 \
 && notify "installed needed OS libs required for Django app"

RUN function notify() { echo -e "\n----[ $1 ]----\n"; } \
 && set -x; su-exec engage:engage ./install-pylibs.sh; set +x \
 && notify "installed/built python libs"
