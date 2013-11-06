#!/bin/bash -e
sudo apt-get install -y cmake make gcc automake libtool

cd /vagrant
mkdir vagrant_build || true
cd vagrant_build
cmake .. -DCMAKE_INSTALL_PREFIX=/usr
make
make install
