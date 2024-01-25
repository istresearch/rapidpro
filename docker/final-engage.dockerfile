# while doing the build, no interaction possible
ARG DEBIAN_FRONTEND=noninteractive

ARG FROM_STAGE
FROM ${FROM_STAGE} as load-files

WORKDIR /opt/code2use
COPY docker/customizations/engage .

# ========================================================================

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
COPY --from=load-files --chown=engage:engage /opt/code2use /opt/ov/brand
RUN rsync -a /opt/ov/brand/ ./ && rm -R /opt/ov/brand

USER engage

RUN echo "STATICFILES_DIRS = (os.path.join(PROJECT_DIR, "engage/static/engage"))" > temba.local_settings.py \
 && python manage.py collectstatic --noinput --settings=temba.settings \
 && rm temba.local_settings.py
