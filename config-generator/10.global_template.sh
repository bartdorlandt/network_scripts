cat >> $OUTPUTFILE << EOF
! Global template
conf t
hostname $VARHOSTNAME
!
service tcp-keepalives-in
service tcp-keepalives-out
service password-encryption
service sequence-numbers
service counters max age 5
no service pad
ip classless
no ip source-route
no ip http server
no ip http secure-server
!
clock timezone CET 1 0
clock summer-time CEST recurring last Sun Mar 2:00 last Sun Oct 3:00  
service timestamps log datetime localtime
service timestamp debug datetime show-timezone localtime 
!
cdp run
!
no ip domain-lookup
ip domain-name nms.local
!
port-channel load-balance src-dst-ip
!
username netadmin privilege 15 secret 0 acce55@1An
enable secret 0 C@nnec1#
!
!!!!!!!!!! crypto key generate, takes time to generate. !!!!!!!!!!!
crypto key generate rsa usage-keys modulus 2048


ip ssh version 2
ip ssh time-out 60
ip ssh auth 3 
ip scp server enable
!
! VTP
vlan internal allocation policy ascending
vtp version 3
vtp domain $VARSITEID
! Only apply this if the complete site has the same hidden commands
!vtp password $VARSITEID hidden
vtp password $VARSITEID 
!
! SNMP
snmp-server community $VARCOMMUNITY RO
snmp-server location $VARSITEID,$VARBUILDING,$VARROOMNUMBER,$VARROOMALIAS
snmp-server contact D&O ICT Technology
snmp-server chassis-id $VARHOSTNAME
snmp-server enable traps 
snmp-server host $VARSNMPHOST $VARHOSTCOMMUNITY
!
! Logging
logging buffered 32768 informational
logging console warnings
logging rate-limit 10
logging trap notifications
logging on
!
! Banner login
!
banner login @
  **************************************************************************
  *                  Unauthorized access is prohibited                     *
  **************************************************************************
  *                                                                        *
  *  This system is to be used only by specifically authorized personnel.  *
  *  Any unauthorized use of the system is unlawful, and may be subject    *
  *  to civil and/or criminal penalties.                                   *
  *                                                                        *
  *  Any use of the system may be logged or monitored without further      *
  *  notice and resulting logs may be used as evidence in court.           *
  **************************************************************************
@
!
! NTP
ntp server 10.89.31.136
ntp server 10.89.63.136
ntp server 10.89.31.137
ntp server 10.89.63.137
!
! Error recovery
errdisable recovery interval 300
errdisable recovery cause psecure-violation
errdisable recovery cause dtp-flap
errdisable recovery cause udld
errdisable recovery cause dhcp-rate-limit
errdisable recovery cause link-flap
!
! Spanning-tree
spanning-tree mode rapid-pvst
spanning-tree extend system-id
spanning-tree portfast bpduguard default
udld aggressive
!
!
interface Vlan1
 description <<< UNUSED >>>
 no ip address
 shutdown
!
line con 0
 location Console port
 exec-timeout 15 0
line vty 0 15
 location RemoteConnection
 exec-timeout 15 0
 transport input ssh
 escape-character 3
line aux 0
 transport input none
 transport output none
 no exec
!
EOF
