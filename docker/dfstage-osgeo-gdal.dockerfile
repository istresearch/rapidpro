ARG FROM_STAGE
FROM ${FROM_STAGE}

RUN apk add --no-cache --virtual .build-deps \
    gcc \
    g++ \
    make \
    cmake \
    libc-dev \
    musl-dev \
    linux-headers

ARG GDAL_VERSION=3.4.2

ADD https://download.osgeo.org/gdal/${GDAL_VERSION}/gdal-${GDAL_VERSION}.tar.gz /tmp

RUN set -ex \
 && cd /tmp \
 && tar xzf gdal-${GDAL_VERSION}.tar.gz \
 && cd gdal-${GDAL_VERSION}

RUN set -ex \
 && ./configure --enable-silent-rules --with-static-proj4=/usr/local/lib

RUN make -s

RUN apk del .build-deps
