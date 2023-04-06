# Alpine image with Python 3.9 as default python3 install
FROM node:16-alpine3.17

# while doing the build, no interaction possible
ARG DEBIAN_FRONTEND=noninteractive

RUN apk add --no-cache \
	bash \
    nano \
    python3 \
	git \
    sqlite \
    tiff \
    curl \
    geos \
    proj \
    gdal \
    binutils \
 && echo -e "\n----[ installed basic needs and runtime osgeo dependencies ]----\n"
