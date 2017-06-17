#!/bin/bash
cat >> $OUTPUTFILE << EOF
!
! L3 switch template
! VTP
vtp mode server
vtp pruning
!
ip routing
!
EOF

if [ "$L3PRIMARY" = "yes" ] ; then
	STPPRIORITY=4096
	HSRPPRIORITY=200
	HSRPOFFSET="1"
	echo "! Make this the primary VTP server" >> $OUTPUTFILE
	echo "do vtp primary" >> $OUTPUTFILE
else
	STPPRIORITY=8192
	HSRPPRIORITY=100
	HSRPOFFSET="2"
fi
#
VLANID=`echo $VARMANINTERFACE | cut -d" " -f2`
SUBNET=`echo $VARSWITCHIPADDRESS|cut -d. -f1,2,3`
if [ "$HSRPREQUIRED" = "yes" ] ; then
	IP=$[$(echo $VARSWITCHIPADDRESS|cut -d. -f4)-1]
else
	IP=$(echo $VARSWITCHIPADDRESS|cut -d. -f4)
fi
#
CREATEVLAN=`echo $VARMANINTERFACE | grep -i vlan`
if [ -n "$CREATEVLAN" ] ; then 
cat >> $OUTPUTFILE << EOF
$VARMANINTERFACE
 name Management
EOF
fi
#
cat >> $OUTPUTFILE << EOF
!
ip route 0.0.0.0 0.0.0.0 $VARDEFAULTGW name Verizon
!
! STP priority
spanning-tree vlan 1-4094 priority $STPPRIORITY
!
int $VARMANINTERFACE
 description *** Network Management ***
 ! vrf forwarding OCW
 ip address $SUBNET.$IP $VARSWITCHMASK
 no ip redirects
 no ip proxy-arp
 no ip route-cache
EOF
#
if [ "$HSRPREQUIRED" = "yes" ] ; then
cat >> $OUTPUTFILE << EOF
 standby $VLANID ip $VARSWITCHIPADDRESS
 standby $VLANID timers 1 4
 standby $VLANID priority $HSRPPRIORITY
 standby $VLANID preempt
EOF
fi
