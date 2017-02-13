#############
PyHydroQuebec
#############

TODO
####

* Add multi account support
* Get the current account balance

Installation
############

::

    pip install pyhydroquebec


Usage
#####

Print your current data

::

    pyhydroquebec -u MYACCOUNT -p MYPASSWORD


Print help

::

    pyhydroquebec -h
    usage: pyhydroquebec [-h] -u USERNAME -p PASSWORD [-j] [-t TIMEOUT]

    optional arguments:
      -h, --help            show this help message and exit
      -u USERNAME, --username USERNAME
                            Hydro Quebec username
      -p PASSWORD, --password PASSWORD
                            Password
      -j, --json            Json output
      -t TIMEOUT, --timeout TIMEOUT
                            Request timeout

Dev env
#######

::

    virtualenv -p /usr/bin/python3.5 env
    pip install -r requirements.txt 
