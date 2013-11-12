#!/bin/sh

export NN_CONFIG_SERVICE=tcp://@master:ip@:10000

exec python2 /code/checkfactor.py --topology="nanoconfig://factor?role=client&ip=@master:ip@" --requests "$1"
