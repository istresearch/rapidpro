ARG FROM_STAGE
ARG FROM_BUILD_LAYER=${FROM_STAGE}
FROM ${FROM_STAGE} as load-files
# while doing the build, no interaction possible
ARG DEBIAN_FRONTEND=noninteractive

WORKDIR /opt/code2use
COPY --chown=engage:engage docker/customizations/engage .

FROM ${FROM_STAGE} as tar_download
ONBUILD RUN echo "download tar"
ARG TAR_URL=LICENSE
ONBUILD ADD "${TAR_URL}" .

# ========================================================================

FROM ${FROM_BUILD_LAYER}
# while doing the build, no interaction possible
ARG DEBIAN_FRONTEND=noninteractive

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
COPY --chown=engage:engage docker/customizations/engage /opt/ov/brand
USER root
RUN rsync -a /opt/ov/brand/ ./ && rm -R /opt/ov/brand

USER engage

# collect and compress static files
ARG RUN_WEB_STATIC_FILE_COLLECTOR=1
RUN if [[ "${RUN_WEB_STATIC_FILE_COLLECTOR}" == "1" ]]; then \
  ./web-static.sh; \
fi
