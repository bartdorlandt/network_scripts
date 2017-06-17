#!/usr/bin/env python3
import argparse
import glob
import os
# import re
import sys
import time
import threading
from queue import Queue

from mylib import libbart as lb


def threader():
    while True:
        # Getting the ip address out of the queue
        worker = q.get()
        if worker is None:
            break
        # print("Worker is: ", worker)
        # starting the other function which does the work
        createconfig(worker, args.delay)
        # completed with the job
        q.task_done()

# def groupvlans2(ip, config):
#     # Create a namedlist of the retrieved vlans
#     # a set of unique vlans that occured more than once.
#     # namedlist = [grdict[x] for x in vlans]
#     namedlist = [grdict[x] for x in vlans if not grdict[x] == 'skip']
#     multilist = set([x for x in namedlist if namedlist.count(x) > 1])
#     # Removing the special keyword 'migrate'.
#     multilist = multilist - {'migrate'}
#     # print(vlan)
#     # temp
#     # vlans.add('7')
#
#     # Create the multi group named vlan config
#     for name in multilist:
#         groupconfiglist = []
#         for x in vlans:
#             if grdict[x] == name:
#                 groupconfiglist.append(int(x))
#         groupconfiglist.sort()
#         config = (config + 'vlan group {} vlan-list {}\n'.format(
#             name, ','.join(map(str, groupconfiglist))))
#         vlans = vlans - set(groupconfiglist)
#
#     return config, staticif


def groupvlans(ip, config, voicevlan):
    # Loading the sh int status
    staticif = []
    vlans = set()
    specialatt = []
    removevlan = []
    # used for the interfaces
    if8021x = []
    # used for the interfaces to deplete for the showing in the configuration
    if8021xshow = []
    try:
        status = lb.getcmdoutput(ip, 'sh int status')
    except:
        print('SSH session failed:', ip)
        print('Error provided:', sys.exc_info()[0])
        status = None
    #
    if not status:
        config = (config +
                  "!\n!\n! group vlan commands can't be added. sh int status \
can't be retrieved. IP: {}\n".format(ip))
        return

    for x in status.split('\n'):
        vlan = x[42:48].rstrip()
        if not vlan:
            # print ('not vlan')
            continue
        elif x.startswith('Po'):
            # print ('Start with Po.\n{}'.format(x))
            continue
        elif '802.1x' in x and x.split()[1] == '802.1x':
            if8021x.append(x.split()[0])
            if8021xshow.append(x.split()[0])
        elif vlan == 'trunk' or vlan == 'routed':
            # print ('Vlan is Trunk\n{}'.format(x))
            staticif.append(x.split()[0])
        elif "Not Present" in x or "SFP" in x:
            # print ('"Not Present" or "SFP"\n{}'.format(x))
            staticif.append(x.split()[0])
        elif "VG" in x and voicevlan in x:
            staticif.append(x.split()[0])
        elif vlan == voicevlan:
            staticif.append(x.split()[0])
        elif vlan[0].isdigit():
            # print ('vlan added {}'.format(vlan))
            vlans.add(vlan)
        else:
            print('Nothing done with {}, \n  IF: {}'.format(ip, x))

    if vlans:
        config = config + '! list of vlans on the switch\n'
    for x in vlans:
        try:
            if grdict[x] == 'skip' and x != '1':
                specialatt.append(x)
            elif (grdict[x] == 'migrate' or
                  grdict[x] == 'remove' or
                  x == '1'):
                continue
            else:
                config = (config +
                          'vlan group {} vlan-list {}\n'.format(grdict[x], x))
        except KeyError as err:
            print("The vlan number doesn't exist in the dictionary. " +
                  "Please check if non-existant vlan numbers are used.\n" +
                  "IP: {}, Wrong vlan number: {}".format(ip, err))

    # Creating a spacer to see which other vlan groups are added.
    config = config + '!\n! other vlans that are unique but not currently \
active on the switch.\n'

    # For the vlans that don't exist on this switch, but are still unique
    # the additional vlan group commands are created.
    vlname, vlnum = [], []
    for x, y in grdict.items():
        if y == 'remove':
            removevlan.append(x)
        elif 'skip' not in y and 'migrate' not in y and voicevlan not in x:
            vlname.append(y)
            vlnum.append(x)

    for x in vlname:
        if vlname.count(x) == 1:
            if vlnum[vlname.index(x)] not in vlans:
                config = (config +
                          'vlan group {} vlan-list {}\n'.format(
                              x, vlnum[vlname.index(x)]))

    # not require since vlan is called 'byod'.

    config = (config + '!\n! Also adding the byod and voice vlan.\n' +
              'vlan group byod vlan-list 913\n' +
              'vlan group voice vlan-list {}\n'.format(voicevlan))

    if if8021xshow:
        config = (config + '! These interfaces are already 802.1x enabled\n')
        while len(if8021xshow) > 6:
            config = config + '! '
            for x in range(6):
                config = config + if8021xshow.pop(0) + ','
            config = config + '\n'
        else:
            config = config + '! '
            for x in range(len(if8021xshow)):
                config = config + if8021xshow.pop(0) + ','
            config = config + '\n'

    if specialatt:
        config = (
            config + '''!\n! Skipped interfaces:\n''')
        for x in status.split('\n'):
            vlan = x[42:48].rstrip()
            if not vlan:
                continue
            elif vlan in specialatt:
                # if 'connect' in x and 'trunk' not in x and 'routed' not in x:
                #     if x.split()[-4] in specialatt:
                staticif.append(x.split()[0])
                config = (config +
                          '! int: {} vlan: {} status: {} desc: {}\n'.format(
                              x.split()[0], x[42:48].rstrip(),
                              x[29:42].rstrip(), x[10:29].rstrip()))

    if removevlan:
        config = (
            config +
            '!\n! vlans which can be removed on the core switch.\n')
        for x in removevlan:
            config = config + '! no vlan {}\n'.format(x)

    # print('staticif: {}'.format(staticif))
    return config, staticif, if8021x


def hardwareconfig(config, sw, ip, macroconf):
    if '8TC' in sw or '12PC' in sw:
        print('{}, applying ROAMING configuration'.format(ip))
        # creating a new config. No group vlans required.
        config = globalconf + globalroaming
    elif '2960' in sw:
        print('{}, applying 2960 configuration'.format(ip))
        config = config + macroconf + globalconf + globalradius + global2960
    elif '3750' in sw or '3560' in sw:
        print('{}, applying 3560/3750 configuration'.format(ip))
        config = config + macroconf + globalconf + globalradius + global3560
    else:
        print('investigate: {}'.format(ip))
    #
    return config


def switchvar(sw):
    if sw in fe:
        ifspeed = 'Fa'
    else:
        ifspeed = 'Gi'
    #
    # is it a stackable switch?
    if ('3560' in sw or '2960-' in sw or 'WS-C2960S-24TS-S' in sw or
            'WS-C2960S-48TS-S' in sw):
        modular = ''
    else:
        modular = '0/'
    #
    ifrange = None
    if '24' in sw:
        ifrange = 24
    elif '48' in sw:
        ifrange = 48
    #
    return ifspeed, modular, ifrange


def getvoicevlan(ip, config):
    # Getting all voice vlans from site info dict
    voicelist = [x for x in grdict.keys() if grdict[x] == 'voice']

    # Return value immideatly if there is only 1 vlan.
    if len(voicelist) == 1:
        return voicelist[0], config

    # Only proceed with the rest if there are more than 1 voice vlan.
    # Get the sh vlan brief from the switch.
    vlanbr = lb.getcmdoutput(ip, 'sh vlan br')
    vlannumber = []
    for vlan in voicelist:
        for x in vlanbr.split('\n'):
            if x and x.split()[0] == vlan:
                if 'Fa' in x or 'Gi' in x:
                    vlannumber.append(vlan)
    if not vlannumber:
        vlannumber.append('200')

    if len(vlannumber) > 1:
        print('Too many voice vlans on same switch. \
            IP: {} voicevlans: {}'.format(ip, vlannumber))
        config = config + '''!\n! Multiple voicevlans found on this switch.
! Please investigate manually.
! For the macro the first vlan is used.
! Voice vlans: {}
!\n'''.format(vlannumber)

    return vlannumber[0], config


def createconfig(ip, delay):
    print('Creating configuration for IP: {:<16} thread name: {}'.format(
        ip, threading.currentThread().getName()))
    # Create an empty configuration
    config = ''

    # Get the voicevlan.
    voicevlan, config = getvoicevlan(ip, config)

    # Creating the macroconf, with a dynamic voice vlan
    macroconf = '''!
macro name ise
 no macro description
 description 802.1x
 switchport mode access
 no switchport access vlan
 switchport voice vlan {}
 authentication control-direction in
 authentication host-mode multi-domain
 authentication order mab dot1x
 authentication priority dot1x mab
 authentication port-control auto
 authentication periodic
 authentication timer reauthenticate 36000
 mab
 no snmp trap link-status
 dot1x pae authenticator
 dot1x timeout held-period 300
 dot1x timeout quiet-period 300
 dot1x timeout ratelimit-period 300
 storm-control broadcast level 2.00
 storm-control multicast level 2.00
 spanning-tree portfast
 spanning-tree guard root
 no spanning-tree bpduguard
 service-policy input Input-Policy
@
'''.format(voicevlan)

    # start with the groupvlans,
    # so we can also get the interfaces we don't want
    config, staticif, if8021x = groupvlans(ip, config, voicevlan)
    # print ('static IF: {}'.format(staticif))

    if os.path.isfile(args.skipinterface):
        config = (config +
                  '!\n! Skipped interfaces as marked in the seperate file.\n')
        with open(args.skipinterface, 'r') as f:
            for line in f:
                if line[0].isdigit() and line.split()[0] == ip:
                    for port in line.lstrip(ip).split(','):
                        staticif.append(port.strip())
                    # print('{}, Ports are skipped: {}'.format(
                    #     ip, line.lstrip(ip).strip()))
                    config = (config +
                              '! ' + line.lstrip(ip).strip() + '\n')
    else:
        print("File doesn't exist: {}".format(args.skipinterface))

    # Get the hostname and devices via SNMP.
    try:
        sw = lb.Switch(ip)
        hostname = sw.gethostname()
        devices = sw.getdevicetype()
    except ConnectionError as err:
        print('SNMP error:', ip, err)
        return
    # Set the filename variable with the hostname variable.
    filename = "{}{}_{}_config.txt".format(outputdir, hostname, ip)

    # Apply the global configurations.
    try:
        config = hardwareconfig(config, devices['sw1'], ip, macroconf)
    except KeyError:
        config = None

    if config:
        # preparing the interface configuration. First clean, than create
        # looping through the stack.
        for stack, switch in enumerate(devices):
            # Setting the variables per switch.
            # Speed may change between members of the stack
            ifspeed, modular, ifrange = switchvar(devices[switch])
            #
            # Only increase the stack number from 0 to 1,
            # if the switch is modular.
            if modular:
                stack += 1

            # Start the configuration of the interfaces.
            if ifrange:
                for port in range(1, ifrange + 1):
                    IF = '{0}{1}/{2}{3}'.format(ifspeed, stack, modular, port)
                    if IF not in staticif and IF not in if8021x:
                        config = config + '''!
default int {0}{1}/{2}{3}
int {0}{1}/{2}{3}
 shut
 {4}
 no shut\n'''.format(ifspeed, stack, modular, port, ifdot1x)

        # write the complete configuration.
        with open(filename, 'w') as f:
            f.write(config)


# Provide switches to control this script
parser = argparse.ArgumentParser(
    description='''This script is used to generate some of the configuration
    required for ISE. It will check the device type and generates a
    configuration accordingly.''',
    epilog='''Bash environment variables used:
    CISCOCOMMUNITY, ACSUSER, ACSPASS,
    ISERADIUSKEY, ISEROAMUSER, ISEROAMPASS''')
parser.add_argument(
    '-i', '--ip', required=True,
    help='''Input should be an IP address, a file containing IP addresses
    or an HPov csv export file. Only the first IP address is used.''')
parser.add_argument(
    '-sc', '--sitecode', required=True,
    help='''Provide the site code.''')
parser.add_argument(
    '-sv', '--sitegroupvlans', required=True,
    help='''Provide the site vlan group overview, so it can be used to create
    the group commands.''')
parser.add_argument(
    '-l2', '--l2vlans', required=True,
    help='''Provide the site l2 vlans overview, so it can be used to create
    the group commands.''')
parser.add_argument(
    '-lp', '--localpsn', required=False, default=None,
    help='''Provide the IP address of the local PSN. If it is provided, you
    also need to provide the closest DC as well. If none is given it
    wont't be used and the PSN's from both DC's are used.''')
parser.add_argument(
    '-si', '--skipinterface', required=False, default=None,
    help='''Get a list of interfaces per device, which need to be skipped.''')
parser.add_argument(
    '-mi', '--managementinterface', required=False, default='vlan 250',
    help='''Provide a different management interface.
    Default is %(default)s.''')
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument(
    '-ams', required=False, default=None, action='store_true',
    help='Provides a true to the closest DC being Amsterdam.')
group.add_argument(
    '-sin', required=False, default=None, action='store_true',
    help='Provides a true to the closest DC being Singapore.')
parser.add_argument(
    '--delay', required=False, type=float, default=1.0,
    help='''Provide an alternative delay factor. Default is %(default)s.''')
args = parser.parse_args()

if not os.path.isfile(args.sitegroupvlans):
    sys.exit("The site group vlan file doesn't exist")
if not os.path.isfile(args.l2vlans):
    sys.exit("The site l2 vlan file doesn't exist")
if args.skipinterface:
    if not os.path.isfile(args.skipinterface):
        sys.exit("The skipinterface file doesn't exist")

# Variables
iplist, iperror = lb.readipfile(args.ip)
acsuser = lb.envvariable("ACSUSER")
acspass = lb.envvariable("ACSPASS")
communitystring = lb.envvariable("CISCOCOMMUNITY")
iseradius = lb.envvariable("ISERADIUSKEY")
iseroamuser = lb.envvariable("ISEROAMUSER")
iseroampass = lb.envvariable("ISEROAMPASS")
processes = 30
q = Queue()
threads = list()
lock = threading.Lock()
searchstring = '*config.txt'
workdir = os.path.expanduser('~') + '/working'
outputdir = '{}/{}_ISEconfig/'.format(workdir, args.sitecode)
mgmtintf = args.managementinterface
# ifignore = '{}/{}_if_ignore'.format(os.path.dirname(args.sitegroupvlans),
#                                     args.sitecode)

# PSN logic
amslbip = '10.215.48.10'
sinlbip = '10.231.92.10'
psn01 = '10.215.48.41'
psn02 = '10.215.48.42'
psn03 = '10.231.92.41'
psn04 = '10.231.92.42'
if args.localpsn and args.ams:
    psnlist = (args.localpsn, amslbip)
    dynauthlist = (args.localpsn, psn01, psn02)
    psnnames = ('LOCALPSN', 'ISE-VIP-Amsterdam')
elif args.localpsn and args.sin:
    psnlist = (args.localpsn, sinlbip)
    dynauthlist = (args.localpsn, psn03, psn04)
    psnnames = ('LOCALPSN', 'ISE-VIP-Singapore')
elif args.ams:
    psnlist = (amslbip, sinlbip)
    dynauthlist = (psn01, psn02, psn03, psn04)
    psnnames = ('ISE-VIP-Amsterdam', 'ISE-VIP-Singapore')
elif args.sin:
    psnlist = (sinlbip, amslbip)
    dynauthlist = (psn03, psn04, psn01, psn02)
    psnnames = ('ISE-VIP-Singapore', 'ISE-VIP-Amsterdam')

# PSN config parts
dynauthconfig = ''
isesrvnameconfig2960 = ''
radiussrvconfig2960 = ''
radiussrvconfig3560 = ''
isesrvnameconfig3560 = ''

for x in psnnames:
    isesrvnameconfig2960 = isesrvnameconfig2960 + ' server name {}\n'.format(x)

for x in dynauthlist:
    dynauthconfig = dynauthconfig + ' client {} server-key {}\n'.format(
        x, iseradius)

for y, x in enumerate(psnlist):
    radiussrvconfig2960 = (
        radiussrvconfig2960 +
        '''radius server {}
 address ipv4 {} auth-port 1812 acct-port 1813
  key {}\n'''.format(psnnames[y], x, iseradius))

    isesrvnameconfig3560 = (
        isesrvnameconfig3560 +
        ' server {} auth-port 1812 acct-port 1813\n'.format(x))

    radiussrvconfig3560 = (
        radiussrvconfig3560 +
        'radius-server host {} auth-port 1812 \
acct-port 1813 key 0 {}\n'.format(
            x, iseradius))

dynauthconfig = dynauthconfig.rstrip('\n')
isesrvnameconfig2960 = isesrvnameconfig2960.rstrip('\n')
radiussrvconfig2960 = radiussrvconfig2960.rstrip('\n')
radiussrvconfig3560 = radiussrvconfig3560.rstrip('\n')
isesrvnameconfig3560 = isesrvnameconfig3560.rstrip('\n')

fe = ('WS-C2960-24TT-L',
      'WS-C2960-48TT-L',
      'WS-C2960-48TC-L',
      'WS-C2960-8TC-L',
      'WS-C3560-24PS',
      'WS-C3560-24TS',
      'WS-C3560-48PS',
      'WS-C3560V2-48PS',
      'WS-C3750-48P',
      'WS-C3750-24P',
      'WS-C3750V2-48PS')

ge = ('WS-C2960X-48FPD-L'
      'WS-C2960S-24PD-L',
      'WS-C2960S-24TD-L',
      'WS-C2960S-48FPD-L',
      'WS-C2960S-48FPS-L',
      'WS-C2960S-48LPD-L',
      'WS-C3560G-24PS',
      'WS-C3560G-24TS',
      'WS-C3750G-48PS',
      'WS-C3750G-24PS',
      'WS-C3750G-24TS-1U',
      'WS-C3750X-12S',
      'WS-C3750X-24',
      'WS-C3750X-24P',
      'WS-C3750X-48P')

# Configuration variables
globalconf = '''!
errdisable recovery cause security-violation
no spanning-tree portfast bpduguard default
ip radius source-interface {}
!
! Service-policy for all ports
mls qos
!
mls qos map policed-dscp 10 18 24 26 46 to 8
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
cisp enable
!
'''.format(mgmtintf)

globalradius = '''!
aaa authentication dot1x default group ISE-PSN
aaa authorization network default group ISE-PSN
aaa authorization auth-proxy default group ISE-PSN
aaa accounting dot1x default start-stop group ISE-PSN
aaa accounting update periodic 5
aaa accounting system default start-stop group ISE-PSN
!
authentication mac-move permit
!
ip device tracking
ip device tracking probe delay 10
!
logging origin-id ip
!
mac address-table notification change
mac address-table notification mac-move
snmp-server enable traps mac-notification
!
epm logging
!
dot1x system-auth-control
dot1x critical eapol
authentication critical recovery delay 1000
!
radius-server attribute 6 on-for-login-auth
radius-server attribute 8 include-in-access-req
radius-server attribute 25 access-request include
!
radius-server vsa send accounting
radius-server vsa send authentication
radius-server dead-criteria time 60 tries 5
radius-server deadtime 20
!
'''

global2960 = '''!
aaa group server radius ISE-PSN
{isesrvnameconfig2960}
!
aaa server radius dynamic-author
{dynauthconfig}
!
{radiussrvconfig2960}
!
'''.format(dynauthconfig=dynauthconfig,
           isesrvnameconfig2960=isesrvnameconfig2960,
           radiussrvconfig2960=radiussrvconfig2960)


global3560 = '''!
aaa group server radius ISE-PSN
{isesrvnameconfig3560}
!
aaa server radius dynamic-author
{dynauthconfig}
!
{radiussrvconfig3560}
!
'''.format(dynauthconfig=dynauthconfig,
           radiussrvconfig3560=radiussrvconfig3560,
           isesrvnameconfig3560=isesrvnameconfig3560)

globalroaming = '''!
! Be carefull, this will probably bring the switch down.
! The upstream port will need to have the native vlan set to default as well.
! spanning-tree value for vlan 1 should be higher than the upstream switch.
!
spanning-tree vlan 1 priority 61440
!
dot1x supplicant force-multicast
!
cisp enable
eap profile EAP_PRO
 method md5
!
dot1x credentials CRED_PRO
 username {}
 password 0 {}
!
interface GigabitEthernet0/1
 description Trunk+dot1x+neat
 switchport mode trunk
 switchport nonegotiate
 logging event trunk-status
 logging event status
 mls qos trus dscp
 dot1x pae supplicant
 dot1x credentials CRED_PRO
 dot1x supplicant eap profile EAP_PRO
 storm-control broadcast level 2.00
 storm-control multicast level 2.00
 no switchport trunk native vlan 250
!
'''.format(iseroamuser, iseroampass)

ifdot1x = 'macro apply ise'

# get the sh int status, to create group commands
# grdict = {}
with open(args.sitegroupvlans, 'r') as a, open(args.l2vlans, 'r') as b:
    f = a.readlines() + b.readlines()
    # for x in f:
    #      grdict[x.split()[0]] = x.split()[1]
    grdict = {x.split()[0]: x.split()[2] for x in f if x[0].isdigit()}

# with open(args.l2vlans, 'r') as f:
#     for x in f:
#         if x[0].isdigit():
#             grdict[x.split()[0]] = x.split()[2]

# Start the script, get the info required
start = time.time()

if not os.path.isdir(outputdir):
    os.mkdir(outputdir)

# Staring an x amount of threads
for x in range(processes):
    # calling the function threader
    t = threading.Thread(target=threader)
    t.start()
    threads.append(t)

print("Total IPs:", len(iplist))
# print(iplist)
if iperror:
    print("Total errors:", len(iperror))
    print('''\n\nThe following lines from the source were not used because of
errors:\n''')
    for x in iperror:
        print(x)

# Putting the IP addresses to the queue
for ip in iplist:
    q.put(ip)

# wait until the thread terminates
q.join()

# stop workers
for i in range(processes):
    q.put(None)
for t in threads:
    t.join()

files = (glob.glob1(outputdir, searchstring))

# end time - start time
print("\nTotal time after input:", time.time() - start)
if not len(iplist) == 0:
    print("Total output files: {}. The output is saved in:".format(
        len(iplist)))
    print("    ", outputdir)

# print(count)
print("\nTotal time after input:", time.time() - start)
