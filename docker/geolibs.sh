#!/bin/sh

set -e # fail on any error

# Versions
# ===================================================================
GEOS_VERSION=3.10.2
PROJ_VERSION=8.2.1    #9.0.0 has known issues with M1, avoid for now.
GDAL_VERSION=3.4.2

# Install geos
# ===================================================================
cd /tmp
wget https://download.osgeo.org/geos/geos-${GEOS_VERSION}.tar.bz2
tar xvjf geos-${GEOS_VERSION}.tar.bz2
cd geos-${GEOS_VERSION}
mkdir _build
cd _build
# Set up the build
cmake \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX=/usr/local \
  -DBUILD_DOCUMENTATION=OFF \
  -DBUILD_SHARED_LIBS=ON \
  -DDISABLE_GEOS_INLINE=OFF \
  ..
# Run the build, test, install
cmake --build .
#ctest --output-on-failure .
cmake --build . --target install

# Install proj
# ===================================================================
cd /tmp
wget https://download.osgeo.org/proj/proj-${PROJ_VERSION}.tar.gz
tar xvzf proj-${PROJ_VERSION}.tar.gz
cd proj-${PROJ_VERSION}
mkdir _build
cd _build
cmake \
  -DCMAKE_BUILD_TYPE=Release \
  -DBUILD_TESTING=OFF \
  ..
cmake --build .
#ctest --output-on-failure .
cmake --build . --target install
projsync --system-directory --all

# Install gdal
# ===================================================================
cd /tmp
wget https://download.osgeo.org/gdal/${GDAL_VERSION}/gdal-${GDAL_VERSION}.tar.gz
tar xzf gdal-${GDAL_VERSION}.tar.gz
cd gdal-${GDAL_VERSION}
./configure --enable-silent-rules --with-static-proj4=/usr/local/lib
make -s
make -s install

# Clean up
# ===================================================================
rm -rf /tmp/*
rm -rf /root/.cache
