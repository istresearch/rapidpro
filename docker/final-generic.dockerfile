ARG STATICFILES_FROM_IMAGE=changeme
FROM ${STATICFILES_FROM_IMAGE} as filesrc

# ========================================================================

ARG FROM_STAGE
FROM ${FROM_STAGE} as load-files

WORKDIR /opt/code2use
COPY docker/customizations/any/web-static-engage.sh .
COPY docker/customizations/generic .

# ========================================================================

FROM ${FROM_STAGE}

ARG VERSION_TAG
ENV VERSION_TAG=${VERSION_TAG:-main}
LABEL org.label-schema.name="Engage" \
      org.label-schema.description="Enabling Global Conversations." \
      org.label-schema.version=${VERSION_TAG} \
      org.label-schema.schema-version="1.0"

# apply branding
COPY --from=load-files --chown=engage:engage /opt/code2use /tmp/appfiles
RUN rsync -a /tmp/appfiles ./ && rm -R /tmp/appfiles || true

# copy over the webapp static files
COPY --from=filesrc /rapidpro/sitestatic /rapidpro/sitestatic

USER engage
