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

RUN set -ex \
 && cd /tmp/geos/_build; cmake --build . --target install \
 && cd /tmp/proj/_build; cmake --build . --target install \
 && cd /tmp \
 && tar xzf gdal-${GDAL_VERSION}.tar.gz \
 && cd gdal-${GDAL_VERSION} \
 && ./configure --enable-silent-rules --with-static-proj4=/usr/local/lib \
 && make -s

RUN apk del .build-deps
