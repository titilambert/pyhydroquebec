#!/bin/sh
set -e

# Config
if [ ! -z "$CONFIG" ]
then
    export CONFIG="/etc/pyhydroquebec.yaml"
fi

mqtt_pyhydroquebec
