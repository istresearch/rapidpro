#!/bin/sh

apk add -U --virtual .rp-build-deps \
	freetype-dev \
	g++ \
 	gcc \
 	git \
 	libc-dev \
 	libffi \
 	libffi-dev \
 	libgcc \
 	libjpeg-turbo-dev \
 	libpng-dev \
 	libressl-dev \
 	libstdc++ \
 	libxml2-dev \
 	libxslt-dev \
 	libzmq \
 	linux-headers \
 	make \
 	musl-dev \
 	ncurses \
 	ncurses-dev \
 	patch \
 	pcre-dev \
 	postgresql-dev \
 	python3-dev \
 	readline \
 	readline-dev \
 	zlib-dev \
 && echo "installed .rp-build-deps"
