ARG FROM_STAGE_TAG
ARG VERSION_TAG

# ========================================================================

FROM istresearch/p4-engage:${FROM_STAGE_TAG}

ARG VERSION_TAG
LABEL org.label-schema.name="Engage" \
      org.label-schema.description="Enabling Global Conversations." \
      org.label-schema.version=$VERSION_TAG \
      org.label-schema.schema-version="1.0"

ENV VERSION_TAG=$VERSION_TAG

# apply branding
COPY --chown=engage:engage docker/customizations/generic /opt/ov/brand
USER root
RUN rsync -a /opt/ov/brand/ ./ && rm -R /opt/ov/brand
USER engage

# compress static files
RUN ./web-static.sh
