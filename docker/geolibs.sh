#!/bin/sh

set -e # fail on any error


# Versions
# ===================================================================
GEOS_VERSION=3.10.2
PROJ_VERSION=9.0.0
PROJ_DATA_VERSION=1.9
GDAL_VERSION=3.4.2


# Install geos
# ===================================================================
cd /tmp
wget https://download.osgeo.org/geos/geos-${GEOS_VERSION}.tar.bz2
tar xjf geos-${GEOS_VERSION}.tar.bz2
cd geos-${GEOS_VERSION}
./configure --enable-silent-rules CFLAGS="-D__sun -D__GNUC__"  CXXFLAGS="-D__GNUC___ -D__sun"
make -s
make -s install


# Install proj
# ===================================================================
cd /tmp
wget https://download.osgeo.org/proj/proj-${PROJ_VERSION}.tar.gz
wget https://download.osgeo.org/proj/proj-data-${PROJ_DATA_VERSION}.tar.gz
tar xzf proj-${PROJ_VERSION}.tar.gz
cd proj-${PROJ_VERSION}/nad
tar xzf ../../proj-data-${PROJ_DATA_VERSION}.tar.gz
cd ..
./configure --enable-silent-rules
make -s
make -s install


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
