ARG FROM_STAGE
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

# v9.0.0 has known issues with M1, avoid for now.
ARG PROJ_VERSION=8.2.1

ADD https://download.osgeo.org/proj/proj-${PROJ_VERSION}.tar.gz /tmp

RUN set -ex \
 && cd /tmp \
 && tar xvzf proj-${PROJ_VERSION}.tar.gz \
 && cd proj-${PROJ_VERSION}
 && mkdir _build && cd _build \
 && cmake \
  -DCMAKE_BUILD_TYPE=Release \
  -DBUILD_TESTING=OFF \
  .. \
 && cmake --build . \
 && echo "Finished build, install ready."

RUN apk del .build-deps
