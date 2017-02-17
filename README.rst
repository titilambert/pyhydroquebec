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

Dev env
#######

::

    virtualenv -p /usr/bin/python3.5 env
    pip install -r requirements.txt 
