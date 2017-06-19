#!/bin/bash
address=`echo $1 | cut -d / -f 3`
port=`echo $1 | cut -d / -f 4`
if [ "$port" == "" ]; then
port=22
fi
putty -ssh ${address} -P ${port}
