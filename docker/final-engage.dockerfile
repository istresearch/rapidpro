ARG FROM_STAGE

ARG STATICFILES_FROM_IMAGE=changeme
FROM ${STATICFILES_FROM_IMAGE} as filesrc

# ========================================================================

ARG FROM_STAGE
FROM ${FROM_STAGE} as load-files

WORKDIR /opt/code2use
COPY docker/customizations/any/web-static-engage.sh .
COPY docker/customizations/engage .

# ========================================================================

ARG FROM_STAGE
FROM ${FROM_STAGE}

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
COPY --from=load-files --chown=engage:engage /opt/code2use ./

COPY --from=filesrc /rapidpro/locale /rapidpro/locale
COPY --from=filesrc /rapidpro/sitestatic /rapidpro/sitestatic

USER engage
