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

ARG GEOS_VERSION=3.10.2

ADD https://download.osgeo.org/geos/geos-${GEOS_VERSION}.tar.bz2 /tmp

RUN set -ex \
 && cd /tmp \
 && tar xvjf geos-${GEOS_VERSION}.tar.bz2 \
 && cd geos-${GEOS_VERSION}

RUN set -ex \
 && mkdir _build && cd _build \
 && cmake \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX=/usr/local \
  -DBUILD_DOCUMENTATION=OFF \
  -DBUILD_SHARED_LIBS=ON \
  -DDISABLE_GEOS_INLINE=OFF \
  ..

RUN cmake --build .
#ctest --output-on-failure .

RUN apk del .build-deps
