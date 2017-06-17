#!/bin/bash
STORMGI="2"
STORMFA="5"

OUTPUTFILE2="$OUTPUTFILE"
OUTPUTFILE="${OUTPUTFILE}_ports"

mod_intro () {
cat > $OUTPUTFILE << EOF
!
! The below show all different kind of ports. These are examples based on the standard. 
! You can apply these on the ports where you need them.
! Some of the ports still require clarity on which VLAN they should belong to in the standard.
!
EOF
}

mod_3750X-48 () {
cat >> $OUTPUTFILE << EOF
!
! 3750X-48 ports layout
! Gi 1/0/1 - 48
! Gi1/1/1 - 4 - SFP module C3KX-NM-1G
!
EOF
}

mod_2960X-48 () {
cat >> $OUTPUTFILE << EOF
!
! 2960X-48 ports layout
! Gi 1/0/1 - 48
! Gi 1/0/49 - 50 - SFP || Te1/0/1 - 2
!
EOF
}

#!!!!! Interface examples !!!!!
mod_server () {
cat >> $OUTPUTFILE << EOF
!
!!!!!!!!!!!!!!!!!!   Server port
interface range GigabitEthernet1/0/X - Y
 description <SERVER NAME> <NIC ID>
 switchport mode access
 switchport access vlan <VLAN NUMBER>
 storm-control broadcast level $STORMGI
 storm-control multicast level $STORMGI
 logging event link-status
 logging event status
 no cdp enable
 spanning-tree portfast
!
!
! Server port with LACP
interface GigabitEthernet1/0/X
 description SERVER NAME NIC-1
 channel-group <#> mode active
interface GigabitEthernet2/0/X
 description SERVER NAME NIC-2
 channel-group <#> mode active
!
interface Port-channel <#>
 description <SERVER NAME>
 switchport access vlan <50-53>
 switchport mode access
 no snmp trap link-status
 spanning-tree portfast
 logging event link-status
 logging event bundle-status
 logging event status
 storm-control broadcast level $STORMGI
 storm-control multicast level $STORMGI
!
EOF
}

mod_face () {
cat >> $OUTPUTFILE << EOF
!
!!!!!!!!!!!!!!!!!!   Face client with Cisco IP phone, vlans 2-8
interface range GigabitEthernet1/0/X - Y
 description FACE-Client
 switchport access vlan <2-8>
 switchport mode access
 switchport voice vlan 200
 switchport port-security maximum 3
 switchport port-security
 switchport port-security aging time 1
 switchport port-security aging type inactivity
 storm-control broadcast level $STORMGI
 storm-control multicast level $STORMGI
 no snmp trap link-status
 spanning-tree portfast
 service-policy input Input-Policy
EOF
}

mod_ap () {
if [ "$SWITCHTYPE" = "L3" ] ; then
  if [ "$L3PRIMARY" = "yes" ] ; then
    cat >> $OUTPUTFILE << EOF
!
! Check on double L3 switches. Will need excluded-addresses
! Primary router
! ip dhcp excluded-address X.X.X.121 X.X.X.254
EOF
  else
    cat >> $OUTPUTFILE << EOF
!
! Secondary router
! ip dhcp excluded-address X.X.X.1 X.X.X.120
! ip dhcp excluded-address X.X.X.250 X.X.X.254
EOF
  fi
  cat >> $OUTPUTFILE << EOF
!
! DHCP Pool for AP management
ip dhcp pool vlan22(AP)
   network <Vlan 22 network address> 255.255.254.0
   default-router <IP address of Vlan22>
   dns-server $VARDNSSERVER
   option 43 hex f104.c0a8.ea82
   option 60 ascii "Cisco AP c3502"
   domain-name $VARSITEID.nms.local
EOF
fi

cat >> $OUTPUTFILE << EOF
!
!!!!!!!!!!!!!!!!!! Access points vlan 20 - 24, 22 usually
interface range GigabitEthernet1/0/X - Y
 description access-point
 switchport access vlan 22
 switchport mode access
 logging event power-inline-status
 storm-control broadcast level $STORMGI
 storm-control multicast level $STORMGI
 spanning-tree portfast
 mls qos trust dscp
EOF
}

mod_hreap () {
if [ "$SWITCHTYPE" = "L3" ] ; then
	if [ "$L3PRIMARY" = "yes" ] ; then
		cat >> $OUTPUTFILE << EOF
!
! Check on double L3 switches. Will need excluded-addresses
! Primary router
! ip dhcp excluded-address X.X.X.121 X.X.X.254
EOF
	else 
		cat >> $OUTPUTFILE << EOF
!
! Secondary router
! ip dhcp excluded-address X.X.X.1 X.X.X.120
! ip dhcp excluded-address X.X.X.250 X.X.X.254
EOF
  fi
cat >> $OUTPUTFILE << EOF
!
! DHCP Pool for AP management, HREAP
ip dhcp pool vlan22(AP)
   network <Vlan 22 network address> 255.255.254.0
   default-router <IP address of Vlan22>
   dns-server $VARDNSSERVER
   option 43 hex f104.c0a8.ea82
   option 60 ascii "Cisco AP c3502"
   domain-name $VARSITEID.nms.local
EOF
fi

#! Access points HREAP
cat >> $OUTPUTFILE << EOF
!
!!!!!!!!!!!!!!!!!! HREAP port
interface range GigabitEthernet1/0/X - Y
 description access-point
 switchport trunk native vlan 22
 switchport mode trunk
 logging event power-inline-status
 switchport nonegotiate
 spanning-tree portfast trunk
 mls qos trust dscp
EOF
}

mod_voice () {
# voice vlan standard is 200
cat >> $OUTPUTFILE << EOF
!
!!!!!!!!!!!!!!!!!! Dedicated Voice 
policy-map Voice-EF
 class class-default
  set dscp ef
!
interface range GigabitEthernet1/0/X - Y
 description VOICE
 switchport access vlan 200
 switchport mode access
 spanning-tree portfast
 switchport port-security maximum 3
 switchport port-security
 switchport port-security aging time 1
 switchport port-security aging type inactivity
 storm-control broadcast level $STORMGI
 storm-control multicast level $STORMGI
 service-policy input Voice-EF
!
EOF
}

mod_video () {
# Video vlan standard is 225
cat >> $OUTPUTFILE << EOF
!
!!!!!!!!!!!!!!!!!! Video conference/Telepresence port
policy-map Video-AF41
 class class-default
  set dscp af41
!
interface range GigabitEthernet1/0/X - Y
 description Telepresence (VC)
 switchport access vlan 225
 switchport mode access
 spanning-tree portfast
 switchport port-security maximum 3
 switchport port-security
 switchport port-security aging time 1
 switchport port-security aging type inactivity
 storm-control broadcast level $STORMGI
 storm-control multicast level $STORMGI
 service-policy input Video-AF41
!
EOF
}

mod_uplink () {
cat >> $OUTPUTFILE << EOF
!!!!!!!!!!!!!!!!!!!!!!!!!! UPLINK ports
! No range. every description is unique
interface GigabitEthernet1/0/X
 description <SWITCH NAME> <INTERFACE> <PoX>
 logging event link-status
 logging event trunk-status
 logging event status 
 mls qos trust dscp
 channel-group <X> mode active
 no shutdown

interface GigabitEthernetX/X/Y
 description <SWITCH NAME> <INTERFACE> <PoX>
 logging event link-status
 logging event trunk-status
 logging event status
 mls qos trust dscp
 channel-group <X> mode active
 no shutdown
!
interface Port-channel<X>
 description <SWITCH NAME> <Po#>
 switchport mode trunk
 switchport trunk native $VARMANINTERFACE
 switchport nonegotiate
 logging event bundle-status
 logging event link-status
 logging event trunk-status
 logging event status
 storm-control broadcast level $STORMGI
 storm-control multicast level $STORMGI
!
EOF
}

mod_unused () {
cat >> $OUTPUTFILE << EOF
!
!!!!!!!!!!!!!!!!!!   Unused ports
int range gi1/0/X - Y
 description <<< UNUSED >>>
 switchport mode access
 shutdown
!
EOF
}

mod_default () {
cat >> $OUTPUTFILE << EOF
!
!!!!!!!!!!!!!!!!!!   Default purpose port
int range gi1/0/X - Y
 description <information>
 switchport mode access
 switchport access vlan <X>
 switchport port-security maximum 3
 switchport port-security
 switchport port-security aging time 1
 switchport port-security aging type inactivity
 storm-control broadcast level $STORMGI
 storm-control multicast level $STORMGI
 spanning-tree portfast
 no cdp enable
!
EOF
}


mod_intro
mod_3750X-48
mod_2960X-48
mod_unused
mod_uplink
mod_face
mod_default
mod_server
mod_ap
mod_hreap
mod_video
mod_voice

#echo "! Make sure to check the DO_SSO_MandatoryBaseline_Routing_Switching document." >> $OUTPUTFILE
echo "output file: ${OUTPUTFILE}"

OUTPUTFILE="$OUTPUTFILE2"
