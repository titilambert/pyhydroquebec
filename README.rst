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

    pyhydroquebec -h
    usage: pyhydroquebec [-h] -u USERNAME -p PASSWORD [-j] [-c CONTRACT] [-l]
                         [-t TIMEOUT]

    optional arguments:
      -h, --help            show this help message and exit
      -u USERNAME, --username USERNAME
                            Hydro Quebec username
      -p PASSWORD, --password PASSWORD
                            Password
      -j, --json            Json output
      -c CONTRACT, --contract CONTRACT
                            Contract number
      -l, --list-contracts  List all your contracts
      -t TIMEOUT, --timeout TIMEOUT
                            Request timeout



Docker
######

::

    docker run -e PYHQ_USER=*** -e PYHQ_PASSWORD=*** ncareau/pyhydroquebec

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

    make test

Or

::

    tox
