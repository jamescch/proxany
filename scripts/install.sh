#!/bin/bash

ver=2.14.0

wget https://www.openvswitch.org/releases/openvswitch-$ver.tar.gz
tar -xzf openvswitch-$ver.tar.gz

sudo apt install -y build-essential libtool autoconf

cd openvswitch-$ver
sudo ./configure
sudo make
sudo make install

sudo rm -rf openvswitch-$ver.tar.gz openvswitch-$ver
