#!/bin/bash
address=`echo $1 | cut -d/ -f3 | cut -d: -f1`
port=`echo $1 | cut -d: -f3`
if [ "$port" == "" ]; then
port=23
fi
putty -telnet ${address} -P ${port}
