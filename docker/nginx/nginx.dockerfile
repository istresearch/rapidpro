ARG STATICFILES_FROM_IMAGE=changeme
FROM ${STATICFILES_FROM_IMAGE} as filesrc

# ========================================================================

FROM nginx:stable-alpine
# while doing the build, no interaction possible
ARG DEBIAN_FRONTEND=noninteractive

# copy over the webapp static files to serve up locally
COPY --from=filesrc /rapidpro/sitestatic /usr/share/nginx/sitestatic
RUN mkdir -p /etc/nginx/env_vars.d \
 && mkdir -p /etc/nginx/nginx-in_events.d
COPY docker/nginx/above_server.d /etc/nginx/above_server.d
COPY docker/nginx/in_server.d /etc/nginx/in_server.d
COPY docker/nginx/nginx.app.conf.template /etc/nginx/templates/
COPY docker/nginx/nginx.conf /etc/nginx/

# default healthcheck grabs a known small file with a fixed ua to avoid spamming access logs
HEALTHCHECK --interval=20s --timeout=3s --retries=10 \
    CMD "curl -m 3 http://localhost/sitestatic/favicon.ico -H 'User-Agent: nginx healthcheck' || exit 1"
