ARG FROM_STAGE
FROM ${FROM_STAGE}
# while doing the build, no interaction possible
ARG DEBIAN_FRONTEND=noninteractive

CMD ["/startup.sh"]

ARG RAPIDPRO_REPO=istresearch/rapidpro
ARG RAPIDPRO_VERSION=main
LABEL org.label-schema.name="RapidPro" \
      org.label-schema.description="RapidPro allows organizations to visually build scalable interactive messaging applications." \
      org.label-schema.url="https://www.rapidpro.io/" \
      org.label-schema.vcs-url="https://github.com/${RAPIDPRO_REPO}" \
      org.label-schema.vendor="Nyaruka, UNICEF, and individual contributors." \
      org.label-schema.version=${RAPIDPRO_VERSION} \
      org.label-schema.schema-version="1.0"

WORKDIR /rapidpro

# apply branding
COPY --chown=engage:engage docker/customizations/rp /opt/ov/brand
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
