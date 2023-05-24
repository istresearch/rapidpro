ARG FROM_STAGE
FROM ${FROM_STAGE}
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

# apply translations
RUN function notify() { echo -e "\n----[ $1 ]----\n"; } \
 && apk -U add --virtual .my-build-deps \
    gettext \
 && notify "installed needed OS libs required to translate stuff" \
 && set -x; ./web-i18n.sh; set +x \
 && apk del .my-build-deps \
 && notify "removed libs only needed for translate stuff"

USER engage

# collect and compress static files
ARG RUN_WEB_STATIC_FILE_COLLECTOR=1
RUN if [[ "${RUN_WEB_STATIC_FILE_COLLECTOR}" == "1" ]]; then \
  ./web-static.sh; \
fi
