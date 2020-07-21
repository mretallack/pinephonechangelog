#!/bin/bash


set -e

if [ "$PYTHON_VERSION" == "" ]
then
	echo "Python version is not defined"
	exit 1
fi

PY_ROOT=`pwd`

rm -f Python-${PYTHON_VERSION}.tar.xz
rm -rf  Python-${PYTHON_VERSION}

wget https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tar.xz


sha256sum --check SHA256SUM 


tar --no-same-owner -xf Python-${PYTHON_VERSION}.tar.xz
cd Python-${PYTHON_VERSION}

patch -p1 < ../F00102-lib64.patch

patch -p1 < ../F00251-change-user-install-location.patch


#patch -p1 < $downloads/python-3.8.1-SUSE-FEDORA-multilib.patch


patch -p1 < ../distutils-reproducible-compile.patch


patch -p1 < ../python-3.3.0b1-localpath.patch


#patch -p0  < $downloads/python-3.3.0b1-localpath.patch
#patch -p0 < $downloads/python-3.3.0b1-curses-panel.patch


# mind this step, otherwise
# none of the modules in `lib-dynload` could be imported !
autoreconf -i



rm -rf build
mkdir build
cd build


LIBLIST="openssl libxml-2.0 libffi libxslt "

for i in $LIBLIST
do
	/usr/bin/pkg-config $i --libs >/dev/null && continue || { echo "$i: Development Library not found."; exit 1; }
done


../configure --prefix=$PY_ROOT/pythonroot-${PYTHON_VERSION} \
             --enable-optimizations --enable-ipv6 --enable-shared \
             --with-system-ffi --with-system-expat \
             --enable-loadable-sqlite-extensions \
             --with-ssl-default-suites=openssl 
             
             
make -j 3

# altinstall, not install (see above)
make altinstall

ln -s python3.8 $PY_ROOT/pythonroot-${PYTHON_VERSION}/bin/python3
ln -s pip3.8 $PY_ROOT/pythonroot-${PYTHON_VERSION}/local/bin/pip3


