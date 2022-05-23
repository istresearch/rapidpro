# Alpine image with Python 3.9 as default python3 install
FROM node:12.22-alpine3.14

RUN set -ex \
 && apk add --no-cache \
	bash nano python3 \
    sqlite \
    tiff \
    curl \
    geos \
    proj \
    gdal \
    binutils \
 && echo "installed basic needs and runtime osgeo dependencies"
