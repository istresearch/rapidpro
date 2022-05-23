ARG FROM_STAGE_TAG
ARG VERSION_TAG

# ========================================================================

FROM istresearch/p4-engage:${FROM_STAGE_TAG}

CMD ["/startup.sh"]

LABEL org.label-schema.name="RapidPro" \
      org.label-schema.description="RapidPro allows organizations to visually build scalable interactive messaging applications." \
      org.label-schema.url="https://www.rapidpro.io/" \
      org.label-schema.vcs-url="https://github.com/$RAPIDPRO_REPO" \
      org.label-schema.vendor="Nyaruka, UNICEF, and individual contributors." \
      org.label-schema.version=$RAPIDPRO_VERSION \
      org.label-schema.schema-version="1.0"

WORKDIR /rapidpro

# apply branding/overrides
COPY --chown=engage:engage docker/customizations/any /opt/ov/any
COPY --chown=engage:engage docker/customizations/rp /opt/ov/brand
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
