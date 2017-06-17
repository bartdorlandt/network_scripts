#!/bin/bash

CONFIG=$1

if [ ! -f "$CONFIG" ] ; then
    echo "Config doesn't exist, exiting."
    exit
fi

#Cisco switches
# Remove enable secret lines
sed -i '/^enable secret/d' $CONFIG
# Remove usernames
sed -i '/^username/d' $CONFIG
# remove line passwords
sed -i '/^ password 7/d' $CONFIG
# SNMP string
sed -i '/snmp community!/d' $CONFIG
#
# Tacacs key
sed -i '/^ key 7 /d' $CONFIG

# VTP password
sed -i '/^VTP Password/d' $CONFIG

#Template
#sed -i '//d' $CONFIG

# Cisco ASA
sed -i '/^enable password/d' $CONFIG
sed -i '/^passwd/d' $CONFIG
sed -i '/^ key /d' $CONFIG
#sed -i '//d' $CONFIG
