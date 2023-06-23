# while doing the build, no interaction possible
ARG DEBIAN_FRONTEND=noninteractive

ARG REPO_UN
ARG REPO_PW
ARG REPO_HOST
ARG REPO_FILEPATH

ARG FROM_STAGE
ARG FROM_BUILD_LAYER=${FROM_STAGE}
FROM ${FROM_STAGE} as load-files

WORKDIR /opt/code2use
COPY docker/customizations/engage .

# ========================================================================

# optional stage in case we already have a collection of static files to use
FROM ${FROM_STAGE} as tar_download
ARG REPO_UN
ARG REPO_PW
ARG REPO_HOST
ARG REPO_FILEPATH
ONBUILD RUN echo "download tar"
ONBUILD ADD --chown=engage:engage "https://${REPO_UN}:${REPO_PW}@${REPO_HOST}/${REPO_FILEPATH}" /rapidpro
ONBUILD RUN TAR_FILE=$(basename "${REPO_FILEPATH}"); \
  if [ -f "${TAR_FILE}" ]; then \
    tar -xzf "${TAR_FILE}"; \
    rm "${TAR_FILE}"; \
  fi

# ========================================================================

FROM ${FROM_BUILD_LAYER}

ARG REPO_UN
ARG REPO_PW
ARG REPO_HOST
ARG REPO_FILEPATH

ARG VERSION_TAG
ENV VERSION_TAG=${VERSION_TAG:-main}
LABEL org.label-schema.name="Engage" \
      org.label-schema.description="Addressing the most urgent human security issues faced by the world’s vulnerable populations." \
      org.label-schema.url="https://twosixtech.com" \
      org.label-schema.vcs-url="https://github.com/istresearch/p4-engage" \
      org.label-schema.vendor="Two Six Technologies" \
      org.label-schema.version=${VERSION_TAG} \
      org.label-schema.schema-version="1.0"

# apply branding
COPY --from=load-files --chown=engage:engage /opt/code2use /opt/ov/brand
USER root
RUN rsync -a /opt/ov/brand/ ./ && rm -R /opt/ov/brand

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
