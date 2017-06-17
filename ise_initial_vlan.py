#!/usr/bin/env python3
import argparse
import os
import sys
import time

from mylib import libbart as lb


# Provide switches to control this script
parser = argparse.ArgumentParser(
    description='''This script is used to create the initial files to be used
    for the mac extract script and other ISE scripts.''',
    epilog="Bash environment variables used: CISCOCOMMUNITY, ACSUSER, ACSPASS")
parser.add_argument(
    '-i', '--ip', required=True,
    help='''Input should be the core IP address, a file containing the IP
    address or an HPov csv export file. Only the first IP address is used.''')
parser.add_argument(
    '-sc', '--sitecode', required=True,
    help='''Provide the site code.''')
parser.add_argument(
    '--delay', required=False, type=float, default=1.0,
    help='''Provide an alternative delay factor. Default is %(default)s.''')
parser.add_argument(
    '-wd', '--workdir', required=False,
    default='{}/ISE_mac'.format(os.path.expanduser('~')),
    help='''Provide the output directory for the files.
    Default is %(default)s.''')
parser.add_argument('--acsprefix', required=False, default=None,
                    help='''Provide a prefix to read a different set of
                    environemnt variables than the default.''')
args = parser.parse_args()

# Variables
acsprefix = args.acsprefix
delay = args.delay
vlanfile = '{}/{}_vlan_group'.format(args.workdir, args.sitecode)
l2vlanfile = '{}/{}_l2_only_vlan'.format(args.workdir, args.sitecode)
vrffile = '{}/{}_vrf'.format(args.workdir, args.sitecode)
ifignorefile = '{}/{}_if_ignore'.format(args.workdir, args.sitecode)

if not os.path.isdir(args.workdir):
    os.mkdir(args.workdir)

# for x in (vlanfile, vrffile, vlgrfile):
for x in (vlanfile, vrffile, ifignorefile, l2vlanfile):
    if os.path.isfile(x):
        sys.exit('Output filename already exists: {}'.format(x))

ovlanfile = open(vlanfile, 'w')
ol2vlanfile = open(l2vlanfile, 'w')
ovrffile = open(vrffile, 'w')
oifignorefile = open(ifignorefile, 'w')
# ovlgrfile = open(vlgrfile, 'w')

iplist, iperror = lb.readipfile(args.ip)
ip = iplist[0]

# Start the script, get the info required
start = time.time()

vlbr = lb.getcmdoutput(ip, 'sh vlan br',
                       delay_factor=delay, acsprefix=acsprefix)
vrfbr = lb.getcmdoutput(ip, 'sh ip vrf',
                        delay_factor=delay, acsprefix=acsprefix)

# list the administratively shut vlans
l3vlshut = lb.getcmdoutput(ip, 'sh ip int brie | i ^Vlan',
                           delay_factor=delay, acsprefix=acsprefix)
l3vlshutlist = [int(x.split()[0].replace('Vlan', ''))
                for x in l3vlshut.split('\n') if "administratively" in x]

ovlanfile.write(
    "! This file is used for the mac extraction" +
    " and creating the switch config.\n" +
    "!\n" +
    "! if ISE_identity_group = noscan,\n" +
    "!      the vlan is not scanned for mac addresses\n" +
    "! if vlan_group_name = skip,\n" +
    "!      the ports belonging to these vlans are not ise-d in the\n" +
    "!      config and the vlan group is not created.\n" +
    "! if vlan_group_name = migrate,\n" +
    "!      the ports belonging to these vlans are ise-d in the config,\n" +
    "!      but the vlan is not used for the vlan group statements\n" +
    "! if vlan_group_name = remove,\n" +
    "!      the ports belonging to these vlans are ise-d in the config,\n" +
    "!      but the vlan is not used for the vlan group statements and it\n" +
    "!      is suggested to remove the vlan from the core switch.\n" +
    "!\n" +
    "! Header\n" +
    "! vlan#  ISE_identity_group  vlan_group_name  comments\n" +
    "!\n")
ol2vlanfile.write(
    "! This file shows the L2 only vlans, which don't have a L3 vlan.\n" +
    "! The same rules apply as per the vlan_group file.\n" +
    "!\n")
ovrffile.write(
    "! This file is listing the VRFs for which you want to do a\n" +
    "! 'sh ip arp vrf x' command, with a VRF per line.\n" +
    "!\n")
oifignorefile.write(
    "! This file can be filled with IP and interfaces which will be " +
    "ignored\n" +
    "! in the generation of the configuration.\n" +
    "!\n" +
    "! Header\n" +
    "! IPaddress Gi1/0/1,Gi2/0/5,Fa3/0/2\n" +
    "!\n")

# Get a list of L2 only vlans
try:
    l2vlans = lb.l2_only_vlans(ip, acsprefix=acsprefix, delay_factor=delay)
except:
    print('Error received:', sys.exc_info()[0])
    sys.exit("Can't get the L2 vlans from the device,\
 is this the correct L3 core switch?")

# walk through the sh vlan br
for x in vlbr.split('\n'):
    if x and x[0].isdigit():
        vlan = x.split()[0]
        name = x[5:38].rstrip()
        if vlan and name:
            if vlan == '1':
                ovlanfile.write('{:<4}  {}  {:<7}  {}   {}\n'.format(
                    vlan, 'noscan', 'migrate', name,
                    "Comment, vlan 1 ports are migrated"))
            elif int(vlan) in l3vlshutlist:
                ol2vlanfile.write('{:<4} {}  {:<7}  {} -- {}\n'.format(
                    vlan, 'noscan', 'skip', name, 'L3 vlan is shut!'))
            elif int(vlan) in l2vlans:
                ol2vlanfile.write('{:<4} {}  {:<7}  {}\n'.format(
                    vlan, 'noscan', 'skip', name))
            else:
                ovlanfile.write('{:<4}  {}  {:<7}  {}\n'.format(
                    vlan, 'noscan', 'skip', name))
            # ovlgrfile.write('{} {} {}\n'.format(vlan, 'notused', name))

# Already adding the new vlans with a ! up front
ol2vlanfile.write('{}{}{}{}{}'.format(
    '! already providing the new (default) ISE vlans\n',
    '!909  noscan  skip     OUI-interconnect\n',
    '!910  noscan  skip     internet-oui\n',
    '!911  noscan  skip     wifi-byod\n',
    '!912  noscan  skip     wifi-guest\n',
    '!913  noscan  skip     byod\n'))

# Put all VRF's into the vrf output file.
for x in vrfbr.split('\n'):
    if x and x.replace('  ', '', 1)[0].isalpha():
        if not (x.split()[0] == 'Name' or
                x.split()[0] == 'Liin-vrf' or
                x.split()[0] == 'mgmtVrf'):
            ovrffile.write('{}\n'.format(x.split()[0]))

ovlanfile.close()
ol2vlanfile.close()
ovrffile.close()
# ovlgrfile.close()

# print(count)
print("\nTotal time after input:", time.time() - start)
print('VLAN outputfile: {}'.format(vlanfile))
print('L2 VLAN outputfile: {}'.format(l2vlanfile))
print('VRF outputfile: {}'.format(vrffile))
print('Interface ignore outputfile: {}'.format(ifignorefile))
# print ('VLAN group outputfile: {}'.format(vlgrfile))
