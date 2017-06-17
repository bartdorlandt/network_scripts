#!/bin/bash
echo ip tacacs source-interface $VARMANINTERFACE >> $OUTPUTFILE

mod_oldtacacs () {
cat >> $OUTPUTFILE << EOF
! TACACS config
tacacs-server host $VARTACACSSERVER1
tacacs-server host $VARTACACSSERVER2
tacacs-server timeout 10
tacacs-server directed-request
tacacs-server key 0 $VARTACACSKEY
EOF
}

mod_newtacacs () {
cat >> $OUTPUTFILE << EOF
! TACACS config
tacacs server TACACS
 address ipv4 $VARTACACSSERVER1
 key $VARTACACSKEY
 timeout 5
tacacs server TACACS_BU
 address ipv4 $VARTACACSSERVER2
 key $VARTACACSKEY
 timeout 5
EOF
}

# setting the default value
CASETACACS=old
# Possibly overwrite the default
if [ "$IOSVERSIONHIGH" == "yes" ] ; then CASETACACS=new ; fi
#if [ -n "$(echo $HARDWARE1 | grep 2960)" ] ; then CASETACACS=old ; fi
if [ -n "$(echo $HARDWARE1 | grep 3750)" ] ; then CASETACACS=new ; fi
if [ -n "$(echo $HARDWARE1 | grep 4500)" ] ; then CASETACACS=new ; fi


case $CASETACACS in 
	old)
		mod_oldtacacs;;
	new)
		mod_newtacacs;;
	*)
		mod_oldtacacs;;
esac
