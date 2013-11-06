#!/bin/bash -e
sudo apt-get install -y cmake make gcc automake libtool

cd /vagrant
rm -rf vagrant_build 2>&1 || true
mkdir vagrant_build
cd vagrant_build
cmake .. -DCMAKE_INSTALL_PREFIX=/usr
make
make install
