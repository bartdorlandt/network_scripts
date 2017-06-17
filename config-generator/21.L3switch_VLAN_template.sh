#!/bin/bash
IPHELPER1="10.207.64.5"
IPHELPER2="10.207.64.6"
IPHELPER3="10.100.44.116"

if [ "$L3PRIMARY" = "yes" ] ; then
  STPPRIORITY=4096
  HSRPPRIORITY=200
  HSRPOFFSET="1"
else
  STPPRIORITY=8192
  HSRPPRIORITY=100
  HSRPOFFSET="2"
fi

cat >> $OUTPUTFILE << EOF
!
! Some vlans, add or remove what is needed
vlan 2
	name FACE-CLIENTS
vlan 9
	name Printers
vlan 200
	name Voice-vlan
vlan 201
	name Interconnect-Vlan
vlan 202
	name WAAS
vlan 240
	name Narrowcasting
vlan 254
	name Fujitsu_Branch_Office_Box
EOF

HSRPIP="1.1.1.254"
MASK="255.255.255.0"
SUBNET=`echo $HSRPIP|cut -d. -f1,2,3`
if [ "$HSRPREQUIRED" = "yes" ] ; then
  IP=$[$(echo $VARSWITCHIPADDRESS|cut -d. -f4)-$HSRPOFFSET]
else
  IP=$(echo $VARSWITCHIPADDRESS|cut -d. -f4)
fi

cat >> $OUTPUTFILE << EOF
!
! Example vlans below, with all options. Modify to your needs.
! HSRP was set to: $HSRPREQUIRED
interface Vlan2
 description FACE Clients
! vrf forwarding OCW
 ip address  $SUBNET.$IP $MASK
 ip helper-address $IPHELPER1
 ip helper-address $IPHELPER2
 ip helper-address $IPHELPER3
 no ip redirects
 no ip proxy-arp
 no ip route-cache
EOF
#
if [ "$HSRPREQUIRED" = "yes" ] ; then
cat >> $OUTPUTFILE << EOF
 standby 2 ip $HSRPIP
 standby 2 timers 1 4
 standby 2 priority $HSRPPRIORITY
 standby 2 preempt
EOF
fi
#
cat >> $OUTPUTFILE << EOF
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! 
!
! Verfy the old environment for (L2)vlans, static routes, access-lists
!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! 
EOF
