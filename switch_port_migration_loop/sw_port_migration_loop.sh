#!/bin/bash

LBEFORE=`cat before | wc -l`
LAFTER=`cat after | wc -l`
ACCESSPORTS=config

if [ ! "${LBEFORE}" = "${LAFTER}" ] ; then
  echo length of the 2 files are not the same
	exit
fi

cat before | cut -c3- > before2
while read -r BEFORE && read -r AFTER <&3 ; do
	echo before = FA $BEFORE
	echo after = $AFTER
	sed -i 's%'FastEthernet${BEFORE}'$%'$AFTER'%' $ACCESSPORTS
done <before2 3<after

rm before2
