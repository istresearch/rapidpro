ARG FROM_STAGE
ARG FROM_GEOS
ARG FROM_PROJ

FROM ${FROM_GEOS} AS stage-geos
FROM ${FROM_PROJ} as stage-proj
FROM ${FROM_STAGE}

RUN apk add --no-cache --virtual .build-deps \
    gcc \
    g++ \
    make \
    cmake \
    libc-dev \
    musl-dev \
    linux-headers \
    sqlite \
    sqlite-dev \
    tiff \
    tiff-dev \
    curl \
    curl-dev

COPY --from=stage-geos /tmp/geos /tmp/geos
COPY --from=stage-proj /tmp/proj /tmp/proj

ARG GDAL_VERSION=3.4.2

ADD https://download.osgeo.org/gdal/${GDAL_VERSION}/gdal-${GDAL_VERSION}.tar.gz /tmp

RUN set -ex \
 && cd /tmp/geos/_build; cmake --build . --target install \
 && cd /tmp/proj/_build; cmake --build . --target install \
 && cd /tmp/proj/_build; projsync --system-directory --all \
 && cd /tmp \
 && tar xzf gdal-${GDAL_VERSION}.tar.gz \
 && mv gdal-${GDAL_VERSION} gdal \
 && cd gdal \
 && ./configure --enable-silent-rules --with-static-proj4=/usr/local/lib \
 && make -s \
 && make -s install

RUN apk del .build-deps \
 && rm -rf /tmp/* \
 && rm -rf /root/.cache
