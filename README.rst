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

NOT WORKING FOR NOW

::

   cp config.yaml.sample config.yaml

Edit config.yaml

::

    MQTT_USERNAME=mqtt_username MQTT_PASSWORD=mqtt_password MQTT_HOST=mqtt_ip MQTT_PORT=mqtt_port CONFIG=config.yaml mqtt_pyhydroquebec



Docker
######

Docker image list: https://gitlab.com/ttblt-hass/pyhydroquebec/container_registry

::

    docker run -e PYHQ_USER=*** -e PYHQ_PASSWORD=*** registry.gitlab.com/ttblt-hass/pyhydroquebec/cli:master

Docker variables
"""""""""

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


Dev env
#######

::

    make env


Run test
########

::

    USERNAME=myhydrousername PASSWORD=myhydropassword tox
