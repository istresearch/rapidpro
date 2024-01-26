# while doing the build, no interaction possible
ARG DEBIAN_FRONTEND=noninteractive

ARG FROM_STAGE
FROM ${FROM_STAGE} as load-files

WORKDIR /opt/code2use
ARG BRAND_NAME=engage
COPY "docker/customizations/${BRAND_NAME}" .

ARG REPO_UN
ARG REPO_PW
ARG REPO_DL_DOMAIN
ARG REPO_FILEPATH
COPY docker/customizations/any/web-static-curl.sh .
RUN function notify() { echo -e "\n----[ $1 ]----\n"; } \
 && if [[ -n "${REPO_DL_DOMAIN}" ]]; then \
  ./web-static-curl.sh; \
  notify "downloaded and extracted static files tarball"; \
fi

ARG USE_WEB_STATIC_FILE=LICENSE
ADD ${USE_WEB_STATIC_FILE} /opt/code2use

# ========================================================================

FROM ${FROM_STAGE}

# apply branding
COPY --from=load-files --chown=engage:engage /opt/code2use /opt/ov/brand
RUN rsync -a /opt/ov/brand/ ./ && rm -R /opt/ov/brand || true

USER engage

# apply translations (needs gettext OS lib)
RUN function notify() { echo -e "\n----[ $1 ]----\n"; } \
 && set -x; ./web-i18n.sh; set +x \
 && notify "translations compiled"

# collect and compress static files
ARG RUN_WEB_STATIC_FILE_COLLECTOR=1
RUN if [[ "${RUN_WEB_STATIC_FILE_COLLECTOR}" == "1" ]]; then \
  ./web-static.sh; \
fi
