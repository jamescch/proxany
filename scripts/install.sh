#!/bin/bash

wget https://www.openvswitch.org/releases/openvswitch-2.14.0.tar.gz
tar -xzf openvswitch-2.14.0.tar.gz

sudo apt install -y build-essential libtool autoconf

sudo ./configure
sudo make
sudo make install