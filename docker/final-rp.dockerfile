ARG FROM_STAGE_TAG
ARG VERSION_TAG

# ========================================================================

FROM istresearch/p4-engage:${FROM_STAGE_TAG}
# while doing the build, no interaction possible
ARG DEBIAN_FRONTEND=noninteractive

CMD ["/startup.sh"]

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
USER engage

# compress static files
RUN ./web-static.sh
