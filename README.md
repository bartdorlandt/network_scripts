# network\_scripts
A collection of network scripts, mostly written in python. Used to retrieve and send information to network devices (mainly cisco)

## ISE
A bunch of these scripts are related to Cisco ISE. They are used to collect MAC address from multiple devices to generate csv files which can be imported into ISE.
The order I use them in for extracting MAC addresses:
1. ise\_initial.py
..* To generate the initial files.
2. ise\_mac\_extract.py (also as a cronjob)
..* To extract the MAC addresses from one or multiple switches

