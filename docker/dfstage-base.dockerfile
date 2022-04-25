# Alpine image with Python 3.9 as default python3 install
FROM node:12.22-alpine3.14

RUN set -ex \
 && apk add --no-cache \
    sqlite \
    tiff \
    curl \
    geos \
    proj \
    gdal \
    binutils \
 && echo "installed runtime osgeo dependencies"
