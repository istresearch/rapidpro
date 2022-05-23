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

# apply branding/overrides
COPY --chown=engage:engage docker/customizations/any /opt/ov/any
COPY --chown=engage:engage docker/customizations/generic /opt/ov/brand
USER root
# copy over the base code
RUN rsync -a /opt/rp/ ./ && rm -R /opt/rp
# overlay with custom/any
RUN rsync -a /opt/ov/any/ ./ && rm -R /opt/ov/any
# overlay with custom/brand
RUN rsync -a /opt/ov/brand/ ./ && rm -R /opt/ov/brand
USER engage

# compress static files
RUN ./web-static.sh
