#!/bin/sh
set -e

# Check user and password
if [ -z "$PYHQ_USER" ] || [ -z "$PYHQ_USER" ]
then
    echo 'Error: No user or password. Set both environnement variables PYHQ_USER and PYHQ_PASSWORD'
    exit 1
fi

# Output type
if [ ! -z "$PYHQ_OUTPUT" ]
then
    case "$PYHQ_OUTPUT" in
        "TEXT") 
            PYHQ_CMD_OUTPUT=""
        ;;
        "JSON")
            PYHQ_CMD_OUTPUT="-j"
        ;;
        "INFLUXDB")
            PYHQ_CMD_OUTPUT="-i"
        ;;
        "CONTRACTS")
            PYHQ_CMD_OUTPUT="-l"
        ;;
    esac
else
    PYHQ_CMD_OUTPUT=""
fi

# Contract
if [ ! -z "$PYHQ_CONTRACT" ]
then
    PYHQ_CMD_CONTRACT="-c $PYHQ_CONTRACT"
fi

# Config
if [ -z "$CONFIG" ]
then
    export CONFIG="/etc/pyhydroquebec/pyhydroquebec.yaml"
fi

if [ "$PYHQ_OUTPUT" = "MQTT"] 
    mqtt_pyhydroquebec
else
    pyhydroquebec -u $PYHQ_USER -p $PYHQ_PASSWORD $PYHQ_CMD_OUTPUT $PYHQ_CMD_CONTRACT
fi
