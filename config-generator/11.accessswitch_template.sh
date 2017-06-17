#!/bin/bash
cat >> $OUTPUTFILE << EOF
!
!
! Access switch template
exception memory ignore overflow io
exception memory ignore overflow processor
no setup express
no vstack
!
no ip routing
spanning-tree vlan 1-4094 priority 32768
!
!$VARMANINTERFACE
! name Management
! VTP
vtp mode client
!
int $VARMANINTERFACE
 description Management
 ip address $VARSWITCHIPADDRESS $VARSWITCHMASK
ip default-gateway $VARDEFAULTGW
!
snmp-server trap-source $VARMANINTERFACE
logging source-interface $VARMANINTERFACE
ntp source $VARMANINTERFACE
!
! MLS QoS
mls qos
!
mls qos map policed-dscp  10 18 24 26 46 to 8
!
ip access-list extended Acl-Bulk-Data
 permit tcp any any eq 22
 permit tcp any any eq 465
 permit tcp any any eq 143
 permit tcp any any eq 993
 permit tcp any any eq 995
 permit tcp any any eq 1914
 permit tcp any any eq ftp
 permit tcp any any eq ftp-data
 permit tcp any any eq smtp
 permit tcp any any eq pop3
!
ip access-list extended Acl-Default
 permit ip any any
!
ip access-list extended Acl-MultiEnhanced-Conf
 permit udp any any range 16384 32767
!
ip access-list extended Acl-Scavanger
 permit tcp any any range 2300 2400
 permit udp any any range 2300 2400
 permit tcp any any range 6881 6999
 permit tcp any any range 28800 29100
 permit tcp any any eq 1214
 permit udp any any eq 1214
 permit tcp any any eq 3689
 permit udp any any eq 3689
 permit tcp any any eq 11999
!
ip access-list extended Acl-Signaling
 permit tcp any any range 2000 2002
 permit tcp any any range 5060 5061
 permit udp any any range 5060 5061
!
ip access-list extended Acl-Transactional-Data
 permit tcp any any eq 443
 permit tcp any any eq 1521
 permit udp any any eq 1521
 permit tcp any any eq 1526
 permit udp any any eq 1526
 permit tcp any any eq 1575
 permit udp any any eq 1575
 permit tcp any any eq 1630
 permit udp any any eq 1630
!
!
class-map match-any Bulk-Data-Class
  match access-group name Acl-Bulk-Data
class-map match-any Multimedia-Conf-Class
  match access-group name Acl-MultiEnhanced-Conf
class-map match-any Voip-Data-Class
  match ip dscp ef
class-map match-any Voip-Signal-Class
  match ip dscp cs3
class-map match-any Default-Class
  match access-group name Acl-Default
class-map match-any Transaction-Class
  match access-group name Acl-Transactional-Data
class-map match-any Scavanger-Class
  match access-group name Acl-Scavanger
class-map match-any Signaling-Class
  match access-group name Acl-Signaling
!
!
policy-map Input-Policy
 class Voip-Data-Class
   set dscp ef
    police 128000 8000 exceed-action policed-dscp-transmit
 class Voip-Signal-Class
   set dscp cs3
    police  32000  8000 exceed-action policed-dscp-transmit
 class Multimedia-Conf-Class
   set dscp af41
    police 5000000 8000 exceed-action drop
 class Bulk-Data-Class
   set dscp af11
    police 10000000 8000 exceed-action policed-dscp-transmit
 class Transaction-Class
   set dscp af21
    police 10000000 8000 exceed-action policed-dscp-transmit
 class Scavanger-Class
   set dscp cs1
    police 10000000 8000 exceed-action policed-dscp-transmit
 class Signaling-Class
   set dscp cs3
    police 32000 8000 exceed-action drop 
 class Default-Class
   set dscp default
    police 10000000 8000 exceed-action policed-dscp-transmit
!
EOF
