#############
PyHydroQuebec
#############


TODO
####

* Add automated tests

Installation
############

::

    pip install pyhydroquebec


Usage
#####

Print your current data

::

    pyhydroquebec -u MYACCOUNT -p MYPASSWORD


List your current contracts

::

    pyhydroquebec -u MYACCOUNT -p MYPASSWORD -l


Print help

::

    usage: pyhydroquebec [-h] [-u USERNAME] [-p PASSWORD] [-j] [-i] [-c CONTRACT]
                        [-l] [-H] [-t TIMEOUT] [-V] [--detailled-energy]
                        [--start-date START_DATE] [--end-date END_DATE]

    optional arguments:
        -h, --help                          show this help message and exit
        -u USERNAME, --username USERNAME    Hydro Quebec username
        -p PASSWORD, --password PASSWORD    Password
        -j, --json                          Json output
        -i, --influxdb                      InfluxDb output
        -c CONTRACT, --contract CONTRACT    Contract number
        -l, --list-contracts                List all your contracts
        -H, --hourly                        Show yesterday hourly consumption
        -t TIMEOUT, --timeout TIMEOUT       Request timeout
        -V, --version                       Show version

    Detailled-energy raw download option:
        --detailled-energy                  Get raw json output download
        --start-date START_DATE             Start date for detailled-output
        --end-date END_DATE                 End date for detailled-output


MQTT DAEMON
###########

::

   cp config.yaml.sample config.yaml

Note: If 'frequency' is not set the "daemon" will collect the data only one time and stop

Edit config.yaml

::

    MQTT_USERNAME=mqtt_username MQTT_PASSWORD=mqtt_password MQTT_HOST=mqtt_ip MQTT_PORT=mqtt_port PYHQ_CONFIG=config.yaml pyhydroquebec -m

Docker
######

Docker image list: https://gitlab.com/ttblt-hass/pyhydroquebec/container_registry

Docker CLI Mode
""""""""""""""""

    ::

        docker run -e PYHQ_USER=*** -e PYHQ_OUTPUT=mqtt -v config.yaml:/etc/pyhydroquebec/pyhydroquebec.yaml registry.gitlab.com/ttblt-hass/pyhydroquebec:master

    **PYHQ_USER** - Required
        `-e PYHQ_USER=myusername`

    **PYHQ_PASSWORD** - Required
        `-e PYHQ_PASSWORD=mypassword`    

    **PYHQ_OUTPUT**

    - `-e PYHQ_OUTPUT=TEXT` - Default
    - `-e PYHQ_OUTPUT=JSON`
    - `-e PYHQ_OUTPUT=INFLUXDB`
    - `-e PYHQ_OUTPUT=CONTRACT`
        
    **PYHQ_CONTRACT**

        `-e PYHQ_CONTRACT=332211223`

Docker MQTT Mode
""""""""""""""""

    ::

        docker run -e MQTT_USERNAME=mqtt_username -e MQTT_PASSWORD=mqtt_password -e MQTT_HOST=127.0.0.1 -e MQTT_PORT=1883 -e PYHQ_OUTPUT=mqtt -v config.yaml:/etc/pyhydroquebec/pyhydroquebec.yaml registry.gitlab.com/ttblt-hass/pyhydroquebec:master

    **MQTT_USERNAME** - Required
        `-e MQTT_USERNAME=myusername`

    **MQTT_PASSWORD** - Required
        `-e MQTT_PASSWORD=mypassword`    

    **MQTT_HOST** - Required
        `-e MQTT_HOST=127.0.0.1`    

    **MQTT_PORT** - Required
        `-e MQTT_PORT=1883`    

    **PYHQ_CONFIG** - Optional
        `-e PYHQ_CONFIG=/etc/pyhydroquebec/pyhydroquebec.yaml` 

Dev env
#######

::

    make env


Run test
########

::

    USERNAME=myhydrousername PASSWORD=myhydropassword tox
